// Reference RAW-VULKAN implementation of the GPU flood-risk pipeline.
//
// The hydraulic time-stepping runs on the GPU as an ITERATED, ping-pong diffusion:
// N_STEPS compute dispatches alternate between two depth buffers, with a storm
// pulse (inlets pinned for the first N_INJECT steps via a per-step push constant,
// then released). Every step's depth field is read back; the peak-momentum step,
// flood intensity (tertile), evacuation difficulty (3-band Dijkstra) and the risk
// matrix are then computed on the host.
#include "flood_risk.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <vulkan/vulkan.h>

#include "risk_spv.h"  // generated from shaders/risk.comp: `risk_spv` (uint32 words)

namespace {

constexpr int DR[4] = {-1, 1, 0, 0};  // up, down, left, right (matches reference)
constexpr int DC[4] = {0, 0, -1, 1};

void check(VkResult r, const char* what) {
    if (r != VK_SUCCESS) {
        throw std::runtime_error(std::string(what) + " failed (VkResult=" +
                                 std::to_string(r) + ")");
    }
}

uint32_t findMemoryType(VkPhysicalDevice phys, uint32_t bits, VkMemoryPropertyFlags props) {
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(phys, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; ++i) {
        if ((bits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & props) == props) {
            return i;
        }
    }
    throw std::runtime_error("no suitable memory type");
}

struct Buffer {
    VkBuffer buffer = VK_NULL_HANDLE;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    VkDeviceSize size = 0;
};

Buffer createHostBuffer(VkPhysicalDevice phys, VkDevice dev, VkDeviceSize size) {
    Buffer b;
    b.size = size;
    VkBufferCreateInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bi.size = size;
    bi.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
    bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    check(vkCreateBuffer(dev, &bi, nullptr, &b.buffer), "vkCreateBuffer");
    VkMemoryRequirements req;
    vkGetBufferMemoryRequirements(dev, b.buffer, &req);
    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = req.size;
    ai.memoryTypeIndex = findMemoryType(
        phys, req.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    check(vkAllocateMemory(dev, &ai, nullptr, &b.memory), "vkAllocateMemory");
    check(vkBindBufferMemory(dev, b.buffer, b.memory, 0), "vkBindBufferMemory");
    return b;
}

void mapWrite(VkDevice dev, const Buffer& b, const void* src) {
    void* p = nullptr;
    check(vkMapMemory(dev, b.memory, 0, b.size, 0, &p), "vkMapMemory");
    std::memcpy(p, src, b.size);
    vkUnmapMemory(dev, b.memory);
}

void mapRead(VkDevice dev, const Buffer& b, void* dst) {
    void* p = nullptr;
    check(vkMapMemory(dev, b.memory, 0, b.size, 0, &p), "vkMapMemory");
    std::memcpy(dst, p, b.size);
    vkUnmapMemory(dev, b.memory);
}

// Push constants for the diffusion shader. Dimensions are passed as floats to
// match the shader's PC block (frows/fcols); inject toggles the inlet pulse.
struct PC { float frows; float fcols; float alpha; float inflow; float inject; };

// speed = VEL_SCALE * |grad(eta)|, eta = bottom + depth, central differences with
// the cell's own eta substituted for out-of-bounds or wall neighbours.
void computeSpeed(const std::vector<float>& bottom, const std::vector<float>& h,
                  const std::vector<float>& openv, int R, int C,
                  std::vector<float>& speed) {
    for (int r = 0; r < R; ++r) {
        for (int c = 0; c < C; ++c) {
            int i = r * C + c;
            if (openv[i] <= 0.5f) { speed[i] = 0.0f; continue; }
            float etaS = bottom[i] + h[i];
            auto etaOr = [&](int nr, int nc) -> float {
                if (nr < 0 || nr >= R || nc < 0 || nc >= C) return etaS;
                int j = nr * C + nc;
                return (openv[j] > 0.5f) ? (bottom[j] + h[j]) : etaS;
            };
            float etaR = etaOr(r, c + 1), etaL = etaOr(r, c - 1);
            float etaU = etaOr(r - 1, c), etaD = etaOr(r + 1, c);
            float gx = (etaR - etaL) * 0.5f;
            float gy = (etaD - etaU) * 0.5f;
            speed[i] = FR_VEL_SCALE * std::sqrt(gx * gx + gy * gy);
        }
    }
}

// Spatial-mean momentum (mean over open cells of depth*speed) at one step.
double meanMomentum(const std::vector<float>& bottom, const std::vector<float>& h,
                    const std::vector<float>& openv, int R, int C) {
    std::vector<float> speed(static_cast<size_t>(R) * C, 0.0f);
    computeSpeed(bottom, h, openv, R, C, speed);
    double sum = 0.0; long cnt = 0;
    for (size_t i = 0; i < h.size(); ++i)
        if (openv[i] > 0.5f) { sum += static_cast<double>(h[i]) * speed[i]; ++cnt; }
    return cnt ? sum / cnt : 0.0;
}

}  // namespace

std::vector<float> floodRisk(const float* bottom, const float* wall,
                             const float* inlet, const float* exit,
                             uint32_t rows, uint32_t cols) {
    const int R = static_cast<int>(rows);
    const int C = static_cast<int>(cols);
    const uint32_t N = rows * cols;

    std::vector<float> bot(bottom, bottom + N);
    std::vector<float> inl(inlet, inlet + N);
    std::vector<float> openv(N);
    for (uint32_t i = 0; i < N; ++i) openv[i] = (wall[i] < 0.5f) ? 1.0f : 0.0f;

    // ---- Vulkan setup (instance / device / compute queue) -------------------
    VkApplicationInfo app{};
    app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app.pApplicationName = "vkflood";
    app.apiVersion = VK_API_VERSION_1_0;
    VkInstanceCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ici.pApplicationInfo = &app;
    VkInstance instance = VK_NULL_HANDLE;
    check(vkCreateInstance(&ici, nullptr, &instance), "vkCreateInstance");

    uint32_t devCount = 0;
    vkEnumeratePhysicalDevices(instance, &devCount, nullptr);
    if (devCount == 0) throw std::runtime_error("no Vulkan physical devices");
    std::vector<VkPhysicalDevice> devs(devCount);
    vkEnumeratePhysicalDevices(instance, &devCount, devs.data());
    VkPhysicalDevice phys = devs[0];

    uint32_t qfCount = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(phys, &qfCount, nullptr);
    std::vector<VkQueueFamilyProperties> qfs(qfCount);
    vkGetPhysicalDeviceQueueFamilyProperties(phys, &qfCount, qfs.data());
    uint32_t computeQF = UINT32_MAX;
    for (uint32_t i = 0; i < qfCount; ++i)
        if (qfs[i].queueFlags & VK_QUEUE_COMPUTE_BIT) { computeQF = i; break; }
    if (computeQF == UINT32_MAX) throw std::runtime_error("no compute queue family");

    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci{};
    qci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    qci.queueFamilyIndex = computeQF;
    qci.queueCount = 1;
    qci.pQueuePriorities = &prio;
    VkDeviceCreateInfo dci{};
    dci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    dci.queueCreateInfoCount = 1;
    dci.pQueueCreateInfos = &qci;
    VkDevice dev = VK_NULL_HANDLE;
    check(vkCreateDevice(phys, &dci, nullptr, &dev), "vkCreateDevice");
    VkQueue queue;
    vkGetDeviceQueue(dev, computeQF, 0, &queue);

    // ---- Buffers: 3 static inputs + rhs + 2 ping-pong eta buffers -----------
    Buffer bufBottom = createHostBuffer(phys, dev, sizeof(float) * N);
    Buffer bufOpen = createHostBuffer(phys, dev, sizeof(float) * N);
    Buffer bufInlet = createHostBuffer(phys, dev, sizeof(float) * N);
    Buffer bufRhs = createHostBuffer(phys, dev, sizeof(float) * N);
    Buffer bufA = createHostBuffer(phys, dev, sizeof(float) * N);
    Buffer bufB = createHostBuffer(phys, dev, sizeof(float) * N);
    mapWrite(dev, bufBottom, bot.data());
    mapWrite(dev, bufOpen, openv.data());
    mapWrite(dev, bufInlet, inl.data());
    // bufRhs, bufA, bufB are written per time step in the implicit solve below.

    // ---- Descriptor set layout: 6 storage buffers (matches risk.comp) -------
    //   0 = bottom, 1 = eta_in, 2 = open, 3 = inlet, 4 = rhs, 5 = eta_out
    VkDescriptorSetLayoutBinding binds[6]{};
    for (int i = 0; i < 6; ++i) {
        binds[i].binding = i;
        binds[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        binds[i].descriptorCount = 1;
        binds[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    }
    VkDescriptorSetLayoutCreateInfo dslci{};
    dslci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dslci.bindingCount = 6;
    dslci.pBindings = binds;
    VkDescriptorSetLayout dsl;
    check(vkCreateDescriptorSetLayout(dev, &dslci, nullptr, &dsl), "vkCreateDescriptorSetLayout");

    VkPushConstantRange pcr{};
    pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    pcr.offset = 0;
    pcr.size = sizeof(PC);
    VkPipelineLayoutCreateInfo plci{};
    plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &dsl;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges = &pcr;
    VkPipelineLayout pl;
    check(vkCreatePipelineLayout(dev, &plci, nullptr, &pl), "vkCreatePipelineLayout");

    VkShaderModuleCreateInfo smci{};
    smci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    smci.codeSize = sizeof(risk_spv);
    smci.pCode = risk_spv;
    VkShaderModule mod;
    check(vkCreateShaderModule(dev, &smci, nullptr, &mod), "vkCreateShaderModule");
    VkPipelineShaderStageCreateInfo st{};
    st.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    st.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    st.module = mod;
    st.pName = "main";
    VkComputePipelineCreateInfo cpci{};
    cpci.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cpci.stage = st;
    cpci.layout = pl;
    VkPipeline pipe;
    check(vkCreateComputePipelines(dev, VK_NULL_HANDLE, 1, &cpci, nullptr, &pipe),
          "vkCreateComputePipelines");

    // Two descriptor sets for the ping-pong: setAB reads A writes B, setBA the reverse.
    VkDescriptorPoolSize psize{};
    psize.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    psize.descriptorCount = 12;  // 6 bindings x 2 sets
    VkDescriptorPoolCreateInfo dpci{};
    dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dpci.maxSets = 2;
    dpci.poolSizeCount = 1;
    dpci.pPoolSizes = &psize;
    VkDescriptorPool descPool;
    check(vkCreateDescriptorPool(dev, &dpci, nullptr, &descPool), "vkCreateDescriptorPool");

    auto allocSet = [&]() {
        VkDescriptorSetAllocateInfo dsai{};
        dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        dsai.descriptorPool = descPool;
        dsai.descriptorSetCount = 1;
        dsai.pSetLayouts = &dsl;
        VkDescriptorSet s;
        check(vkAllocateDescriptorSets(dev, &dsai, &s), "vkAllocateDescriptorSets");
        return s;
    };
    auto bindSet = [&](VkDescriptorSet s, VkBuffer etaIn, VkBuffer etaOut) {
        VkBuffer bufs[6] = {bufBottom.buffer, etaIn, bufOpen.buffer, bufInlet.buffer,
                            bufRhs.buffer, etaOut};
        VkDescriptorBufferInfo dbi[6]{};
        VkWriteDescriptorSet w[6]{};
        for (int i = 0; i < 6; ++i) {
            dbi[i].buffer = bufs[i];
            dbi[i].offset = 0;
            dbi[i].range = VK_WHOLE_SIZE;
            w[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w[i].dstSet = s;
            w[i].dstBinding = i;
            w[i].descriptorCount = 1;
            w[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            w[i].pBufferInfo = &dbi[i];
        }
        vkUpdateDescriptorSets(dev, 6, w, 0, nullptr);
    };
    VkDescriptorSet setAB = allocSet();  // eta_in = A -> eta_out = B
    VkDescriptorSet setBA = allocSet();  // eta_in = B -> eta_out = A
    bindSet(setAB, bufA.buffer, bufB.buffer);
    bindSet(setBA, bufB.buffer, bufA.buffer);

    VkCommandPoolCreateInfo cmdpci{};
    cmdpci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    cmdpci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    cmdpci.queueFamilyIndex = computeQF;
    VkCommandPool cmdPool;
    check(vkCreateCommandPool(dev, &cmdpci, nullptr, &cmdPool), "vkCreateCommandPool");
    VkCommandBufferAllocateInfo cbai{};
    cbai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cbai.commandPool = cmdPool;
    cbai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cbai.commandBufferCount = 1;
    VkCommandBuffer cmd;
    check(vkAllocateCommandBuffers(dev, &cbai, &cmd), "vkAllocateCommandBuffers");
    VkFenceCreateInfo fci{};
    fci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    VkFence fence;
    check(vkCreateFence(dev, &fci, nullptr, &fence), "vkCreateFence");

    const uint32_t gx = (cols + 15u) / 16u;
    const uint32_t gy = (rows + 15u) / 16u;

    auto runSweep = [&](VkDescriptorSet set, const PC& pc) {
        check(vkResetCommandBuffer(cmd, 0), "vkResetCommandBuffer");
        VkCommandBufferBeginInfo bi{};
        bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(vkBeginCommandBuffer(cmd, &bi), "vkBeginCommandBuffer");
        vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipe);
        vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pl, 0, 1, &set, 0, nullptr);
        vkCmdPushConstants(cmd, pl, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(pc), &pc);
        vkCmdDispatch(cmd, gx, gy, 1);
        check(vkEndCommandBuffer(cmd), "vkEndCommandBuffer");
        VkSubmitInfo si{};
        si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
        si.commandBufferCount = 1;
        si.pCommandBuffers = &cmd;
        check(vkResetFences(dev, 1, &fence), "vkResetFences");
        check(vkQueueSubmit(queue, 1, &si, fence), "vkQueueSubmit");
        check(vkWaitForFences(dev, 1, &fence, VK_TRUE, UINT64_MAX), "vkWaitForFences");
    };

    // ---- Stage 1: implicit (backward-Euler) diffusion via Jacobi sweeps ------
    // Per step: rhs = eta^n = bottom + hc; solve (I - ALPHA*L) eta = rhs by N_JACOBI
    // Jacobi sweeps (ping-pong eta in A/B), starting from eta = rhs; then extract
    // depth = max(eta - bottom, 0). Keep every step's depth field.
    std::vector<float> hcur(N, 0.0f), rhs(N), etaInit(N), etaFinal(N);
    std::vector<std::vector<float>> fields;
    fields.reserve(FR_N_STEPS);
    for (int t = 0; t < FR_N_STEPS; ++t) {
        const bool inject = (t < FR_N_INJECT);
        for (uint32_t i = 0; i < N; ++i) {
            float hc = (inject && inl[i] > 0.5f) ? FR_INFLOW : hcur[i];
            rhs[i] = bot[i] + hc;
            etaInit[i] = rhs[i];  // Jacobi starts from eta = rhs (= eta^n)
        }
        mapWrite(dev, bufRhs, rhs.data());
        mapWrite(dev, bufA, etaInit.data());
        PC pc{static_cast<float>(R), static_cast<float>(C), FR_ALPHA, FR_INFLOW,
              inject ? 1.0f : 0.0f};
        const Buffer* lastOut = &bufA;
        for (int k = 0; k < FR_N_JACOBI; ++k) {
            bool even = (k % 2 == 0);
            runSweep(even ? setAB : setBA, pc);
            lastOut = even ? &bufB : &bufA;
        }
        mapRead(dev, *lastOut, etaFinal.data());
        std::vector<float> field(N);
        for (uint32_t i = 0; i < N; ++i) {
            if (openv[i] <= 0.5f) field[i] = 0.0f;            // wall
            else if (inject && inl[i] > 0.5f) field[i] = FR_INFLOW;  // inlet depth pinned
            else { float d = etaFinal[i] - bot[i]; field[i] = d > 0.0f ? d : 0.0f; }
        }
        hcur = field;
        fields.push_back(std::move(field));
    }

    // ---- Stage 2: peak-momentum time (argmax of spatial-mean momentum) -------
    int tstar = 0; double best = -1.0;
    for (int t = 0; t < FR_N_STEPS; ++t) {
        double m = meanMomentum(bot, fields[t], openv, R, C);
        if (m > best) { best = m; tstar = t; }
    }
    const std::vector<float>& h = fields[tstar];

    // ---- Stage 3: flood intensity (Beffa), tertile-classified over open cells -
    std::vector<float> speed(N, 0.0f);
    computeSpeed(bot, h, openv, R, C, speed);
    std::vector<float> fi(N, 0.0f), fiVals;
    fiVals.reserve(N);
    for (uint32_t i = 0; i < N; ++i) {
        if (openv[i] <= 0.5f) continue;
        fi[i] = h[i] * std::max(1.0f, speed[i]);
        fiVals.push_back(fi[i]);
    }
    std::sort(fiVals.begin(), fiVals.end());
    float f1 = 0.0f, f2 = 0.0f;
    int nf = static_cast<int>(fiVals.size());
    if (nf > 0) {
        int i1 = std::min(std::max(static_cast<int>(std::ceil(nf / 3.0)) - 1, 0), nf - 1);
        int i2 = std::min(std::max(static_cast<int>(std::ceil(2.0 * nf / 3.0)) - 1, 0), nf - 1);
        f1 = fiVals[i1]; f2 = fiVals[i2];
    }
    std::vector<int> fil(N, 0);
    for (uint32_t i = 0; i < N; ++i) {
        if (openv[i] <= 0.5f) continue;
        fil[i] = (fi[i] < f1) ? 1 : ((fi[i] < f2) ? 2 : 3);
    }

    // ---- Stage 4: evacuation difficulty (3-band weighted Dijkstra + tertiles) -
    const int64_t BIG = static_cast<int64_t>(1) << 30;
    std::vector<int64_t> dist(N, BIG);
    std::vector<int> cost(N);
    for (uint32_t i = 0; i < N; ++i)
        cost[i] = (h[i] < FR_WADE_LOW) ? FR_COST_SHALLOW
                  : ((h[i] < FR_WADE_HIGH) ? FR_COST_MID : FR_COST_DEEP);
    using QI = std::pair<int64_t, int>;
    std::priority_queue<QI, std::vector<QI>, std::greater<QI>> pq;
    for (uint32_t i = 0; i < N; ++i)
        if (exit[i] > 0.5f && openv[i] > 0.5f) { dist[i] = 0; pq.push({0, static_cast<int>(i)}); }
    while (!pq.empty()) {
        QI top = pq.top(); pq.pop();
        int64_t d = top.first; int i = top.second;
        if (d > dist[i]) continue;
        int r = i / C, c = i % C;
        for (int k = 0; k < 4; ++k) {
            int nr = r + DR[k], nc = c + DC[k];
            if (nr < 0 || nr >= R || nc < 0 || nc >= C) continue;
            int j = nr * C + nc;
            if (openv[j] > 0.5f) {
                int64_t nd = d + cost[j];  // cost to ENTER the neighbour
                if (nd < dist[j]) { dist[j] = nd; pq.push({nd, j}); }
            }
        }
    }
    std::vector<int64_t> reachT;
    for (uint32_t i = 0; i < N; ++i)
        if (openv[i] > 0.5f && dist[i] < BIG) reachT.push_back(dist[i]);
    std::sort(reachT.begin(), reachT.end());
    int64_t t1 = 0, t2 = 0;
    int n = static_cast<int>(reachT.size());
    if (n > 0) {
        int i1 = std::min(std::max(static_cast<int>(std::ceil(n / 3.0)) - 1, 0), n - 1);
        int i2 = std::min(std::max(static_cast<int>(std::ceil(2.0 * n / 3.0)) - 1, 0), n - 1);
        t1 = reachT[i1];
        t2 = reachT[i2];
    }

    // ---- Stage 5: risk = clamp(FI_level + difficulty - 1, 1, 5) -------------
    std::vector<float> out(N, 0.0f);
    for (uint32_t i = 0; i < N; ++i) {
        if (openv[i] <= 0.5f) continue;
        int diff;
        // Half-open bands, consistent with the FI tertile (strict `<`).
        if (dist[i] >= BIG) diff = 3;
        else if (dist[i] < t1) diff = 1;
        else if (dist[i] < t2) diff = 2;
        else diff = 3;
        int risk = fil[i] + diff - 1;
        if (risk < 1) risk = 1;
        if (risk > 5) risk = 5;
        out[i] = static_cast<float>(risk);
    }

    // ---- Teardown -----------------------------------------------------------
    vkDestroyFence(dev, fence, nullptr);
    vkDestroyCommandPool(dev, cmdPool, nullptr);
    vkDestroyDescriptorPool(dev, descPool, nullptr);
    vkDestroyPipeline(dev, pipe, nullptr);
    vkDestroyShaderModule(dev, mod, nullptr);
    vkDestroyPipelineLayout(dev, pl, nullptr);
    vkDestroyDescriptorSetLayout(dev, dsl, nullptr);
    for (Buffer* b : {&bufBottom, &bufOpen, &bufInlet, &bufRhs, &bufA, &bufB}) {
        vkDestroyBuffer(dev, b->buffer, nullptr);
        vkFreeMemory(dev, b->memory, nullptr);
    }
    vkDestroyDevice(dev, nullptr);
    vkDestroyInstance(instance, nullptr);
    return out;
}
