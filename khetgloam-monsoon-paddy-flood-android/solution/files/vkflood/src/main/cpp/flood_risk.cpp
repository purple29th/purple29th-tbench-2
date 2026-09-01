// Khetgloam paddy flood risk — Kerala terraces monsoon implementation
// Raw Vulkan GPU hydraulics for OUSB offline tablets.
// Same 5-stage pipeline as ref but calibrated for paddy silt/bund breaches:
//   stage1: implicit (I-ALPHA*L) via Jacobi N_JACOBI sweeps, inlet pinned
//   INFLOW
//           first N_INJECT steps (bund breach pulse), then released.
//   stage2: peak momentum (spatial mean depth*speed) interior argmax
//   stage3: Beffa FI = depth*max(1,speed) tertiled
//   stage4: 3-band wading cost Dijkstra 2/4/6 at 1.0/1.6m (paddy)
//   stage5: risk = clamp(FI+difficulty-1,1,5) walls 0
// Author: purple29th — individualized for Kerala Khetgloam monsoon story.
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

#include "risk_spv.h"

namespace {

constexpr int K_DR[4] = {-1, 1, 0, 0};
constexpr int K_DC[4] = {0, 0, -1, 1};

void vkCheck(VkResult r, const char *op) {
  if (r != VK_SUCCESS) {
    throw std::runtime_error(std::string("Khetgloam VK ") + op +
                             " err=" + std::to_string(r));
  }
}

uint32_t findMemType(VkPhysicalDevice pdev, uint32_t bits,
                     VkMemoryPropertyFlags need) {
  VkPhysicalDeviceMemoryProperties mp;
  vkGetPhysicalDeviceMemoryProperties(pdev, &mp);
  for (uint32_t i = 0; i < mp.memoryTypeCount; ++i) {
    if ((bits & (1u << i)) && (mp.memoryTypes[i].propertyFlags & need) == need)
      return i;
  }
  throw std::runtime_error("Khetgloam no mem type");
}

struct KBuf {
  VkBuffer buf = VK_NULL_HANDLE;
  VkDeviceMemory mem = VK_NULL_HANDLE;
  VkDeviceSize sz = 0;
};

KBuf makeHostBuf(VkPhysicalDevice pd, VkDevice dev, VkDeviceSize sz) {
  KBuf b;
  b.sz = sz;
  VkBufferCreateInfo bci{};
  bci.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
  bci.size = sz;
  bci.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
  bci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
  vkCheck(vkCreateBuffer(dev, &bci, nullptr, &b.buf), "CreateBuffer paddy");
  VkMemoryRequirements mr;
  vkGetBufferMemoryRequirements(dev, b.buf, &mr);
  VkMemoryAllocateInfo ai{};
  ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
  ai.allocationSize = mr.size;
  ai.memoryTypeIndex = findMemType(pd, mr.memoryTypeBits,
                                   VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                                       VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
  vkCheck(vkAllocateMemory(dev, &ai, nullptr, &b.mem), "Alloc paddy");
  vkCheck(vkBindBufferMemory(dev, b.buf, b.mem, 0), "Bind paddy");
  return b;
}

void kWrite(VkDevice dev, const KBuf &b, const void *src) {
  void *p = nullptr;
  vkCheck(vkMapMemory(dev, b.mem, 0, b.sz, 0, &p), "MapWrite paddy");
  std::memcpy(p, src, b.sz);
  vkUnmapMemory(dev, b.mem);
}
void kRead(VkDevice dev, const KBuf &b, void *dst) {
  void *p = nullptr;
  vkCheck(vkMapMemory(dev, b.mem, 0, b.sz, 0, &p), "MapRead paddy");
  std::memcpy(dst, p, b.sz);
  vkUnmapMemory(dev, b.mem);
}

struct KPC {
  float fr;
  float fc;
  float alpha;
  float inflow;
  float inject;
};

// Paddy water speed: VEL_SCALE * |grad(bottom+depth)| self at wall/OOB
void khetSpeed(const std::vector<float> &bottom, const std::vector<float> &h,
               const std::vector<float> &isOpen, int R, int C,
               std::vector<float> &outSp) {
  for (int r = 0; r < R; ++r) {
    for (int c = 0; c < C; ++c) {
      int i = r * C + c;
      if (isOpen[i] <= 0.5f) {
        outSp[i] = 0.0f;
        continue;
      }
      float es = bottom[i] + h[i];
      auto eAt = [&](int nr, int nc) -> float {
        if (nr < 0 || nr >= R || nc < 0 || nc >= C)
          return es;
        int j = nr * C + nc;
        return (isOpen[j] > 0.5f) ? (bottom[j] + h[j]) : es;
      };
      float er = eAt(r, c + 1), el = eAt(r, c - 1);
      float eu = eAt(r - 1, c), ed = eAt(r + 1, c);
      float gx = (er - el) * 0.5f;
      float gy = (ed - eu) * 0.5f;
      outSp[i] = FR_VEL_SCALE * std::sqrt(gx * gx + gy * gy);
    }
  }
}

double khetMomentum(const std::vector<float> &bottom,
                    const std::vector<float> &h,
                    const std::vector<float> &isOpen, int R, int C) {
  std::vector<float> sp(static_cast<size_t>(R) * C, 0.0f);
  khetSpeed(bottom, h, isOpen, R, C, sp);
  double sum = 0.0;
  long cnt = 0;
  for (size_t i = 0; i < h.size(); ++i)
    if (isOpen[i] > 0.5f) {
      sum += double(h[i]) * sp[i];
      ++cnt;
    }
  return cnt ? sum / cnt : 0.0;
}

} // namespace

std::vector<float> floodRisk(const float *bottom, const float *wall,
                             const float *inlet, const float *exit,
                             uint32_t rows, uint32_t cols) {
  const int R = int(rows);
  const int C = int(cols);
  const uint32_t N = rows * cols;

  std::vector<float> bot(bottom, bottom + N);
  std::vector<float> inGrid(inlet, inlet + N);
  std::vector<float> openF(N);
  for (uint32_t i = 0; i < N; ++i)
    openF[i] = (wall[i] < 0.5f) ? 1.0f : 0.0f;

  // Vulkan — instance / phys / logical compute
  VkApplicationInfo app{};
  app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app.pApplicationName = "khetgloam-paddy";
  app.apiVersion = VK_API_VERSION_1_0;
  VkInstanceCreateInfo ici{};
  ici.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  ici.pApplicationInfo = &app;
  VkInstance inst = VK_NULL_HANDLE;
  vkCheck(vkCreateInstance(&ici, nullptr, &inst), "CreateInstance khet");

  uint32_t pdCount = 0;
  vkEnumeratePhysicalDevices(inst, &pdCount, nullptr);
  if (pdCount == 0)
    throw std::runtime_error("khetgloam no VK phys");
  std::vector<VkPhysicalDevice> pds(pdCount);
  vkEnumeratePhysicalDevices(inst, &pdCount, pds.data());
  VkPhysicalDevice pdev = pds[0];

  uint32_t qfN = 0;
  vkGetPhysicalDeviceQueueFamilyProperties(pdev, &qfN, nullptr);
  std::vector<VkQueueFamilyProperties> qfs(qfN);
  vkGetPhysicalDeviceQueueFamilyProperties(pdev, &qfN, qfs.data());
  uint32_t compQF = UINT32_MAX;
  for (uint32_t i = 0; i < qfN; ++i)
    if (qfs[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
      compQF = i;
      break;
    }
  if (compQF == UINT32_MAX)
    throw std::runtime_error("khetgloam no computeqf");

  float prio = 1.0f;
  VkDeviceQueueCreateInfo qci{};
  qci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
  qci.queueFamilyIndex = compQF;
  qci.queueCount = 1;
  qci.pQueuePriorities = &prio;
  VkDeviceCreateInfo dci{};
  dci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  dci.queueCreateInfoCount = 1;
  dci.pQueueCreateInfos = &qci;
  VkDevice dev = VK_NULL_HANDLE;
  vkCheck(vkCreateDevice(pdev, &dci, nullptr, &dev), "CreateDevice khet");
  VkQueue q;
  vkGetDeviceQueue(dev, compQF, 0, &q);

  // Buffers: bottom, open, inlet static + rhs + pingpong A/B
  KBuf bBottom = makeHostBuf(pdev, dev, sizeof(float) * N);
  KBuf bOpen = makeHostBuf(pdev, dev, sizeof(float) * N);
  KBuf bInlet = makeHostBuf(pdev, dev, sizeof(float) * N);
  KBuf bRhs = makeHostBuf(pdev, dev, sizeof(float) * N);
  KBuf bA = makeHostBuf(pdev, dev, sizeof(float) * N);
  KBuf bB = makeHostBuf(pdev, dev, sizeof(float) * N);
  kWrite(dev, bBottom, bot.data());
  kWrite(dev, bOpen, openF.data());
  kWrite(dev, bInlet, inGrid.data());

  // Descriptor: 6 storage (bottom, eta_in, open, inlet, rhs, eta_out) matches
  // risk.comp
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
  vkCheck(vkCreateDescriptorSetLayout(dev, &dslci, nullptr, &dsl), "DSL khet");

  VkPushConstantRange pcr{};
  pcr.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
  pcr.offset = 0;
  pcr.size = sizeof(KPC);
  VkPipelineLayoutCreateInfo plci{};
  plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
  plci.setLayoutCount = 1;
  plci.pSetLayouts = &dsl;
  plci.pushConstantRangeCount = 1;
  plci.pPushConstantRanges = &pcr;
  VkPipelineLayout pl;
  vkCheck(vkCreatePipelineLayout(dev, &plci, nullptr, &pl), "PipeLayout khet");

  VkShaderModuleCreateInfo smci{};
  smci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
  smci.codeSize = sizeof(risk_spv);
  smci.pCode = risk_spv;
  VkShaderModule mod;
  vkCheck(vkCreateShaderModule(dev, &smci, nullptr, &mod), "Shader khet");
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
  vkCheck(
      vkCreateComputePipelines(dev, VK_NULL_HANDLE, 1, &cpci, nullptr, &pipe),
      "ComputePipe khet");

  VkDescriptorPoolSize ps{};
  ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
  ps.descriptorCount = 12;
  VkDescriptorPoolCreateInfo dpci{};
  dpci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
  dpci.maxSets = 2;
  dpci.poolSizeCount = 1;
  dpci.pPoolSizes = &ps;
  VkDescriptorPool dpool;
  vkCheck(vkCreateDescriptorPool(dev, &dpci, nullptr, &dpool), "DescPool khet");

  auto allocOne = [&]() {
    VkDescriptorSetAllocateInfo dsai{};
    dsai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dsai.descriptorPool = dpool;
    dsai.descriptorSetCount = 1;
    dsai.pSetLayouts = &dsl;
    VkDescriptorSet s;
    vkCheck(vkAllocateDescriptorSets(dev, &dsai, &s), "AllocSet khet");
    return s;
  };
  auto bindTwo = [&](VkDescriptorSet s, VkBuffer etaIn, VkBuffer etaOut) {
    VkBuffer bufs[6] = {bBottom.buf, etaIn,    bOpen.buf,
                        bInlet.buf,  bRhs.buf, etaOut};
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
  VkDescriptorSet setAB = allocOne();
  VkDescriptorSet setBA = allocOne();
  bindTwo(setAB, bA.buf, bB.buf);
  bindTwo(setBA, bB.buf, bA.buf);

  VkCommandPoolCreateInfo cpci2{};
  cpci2.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
  cpci2.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
  cpci2.queueFamilyIndex = compQF;
  VkCommandPool cpool;
  vkCheck(vkCreateCommandPool(dev, &cpci2, nullptr, &cpool), "CmdPool khet");
  VkCommandBufferAllocateInfo cbai{};
  cbai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
  cbai.commandPool = cpool;
  cbai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
  cbai.commandBufferCount = 1;
  VkCommandBuffer cmd;
  vkCheck(vkAllocateCommandBuffers(dev, &cbai, &cmd), "CmdBuf khet");
  VkFenceCreateInfo fci{};
  fci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
  VkFence fence;
  vkCheck(vkCreateFence(dev, &fci, nullptr, &fence), "Fence khet");

  uint32_t gx = (cols + 15u) / 16u;
  uint32_t gy = (rows + 15u) / 16u;

  auto sweep = [&](VkDescriptorSet ds, const KPC &pc) {
    vkCheck(vkResetCommandBuffer(cmd, 0), "ResetCmd khet");
    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkCheck(vkBeginCommandBuffer(cmd, &bi), "Begin khet");
    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipe);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pl, 0, 1, &ds,
                            0, nullptr);
    vkCmdPushConstants(cmd, pl, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(pc),
                       &pc);
    vkCmdDispatch(cmd, gx, gy, 1);
    vkCheck(vkEndCommandBuffer(cmd), "End khet");
    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cmd;
    vkCheck(vkResetFences(dev, 1, &fence), "ResetFence khet");
    vkCheck(vkQueueSubmit(q, 1, &si, fence), "Submit khet");
    vkCheck(vkWaitForFences(dev, 1, &fence, VK_TRUE, UINT64_MAX), "Wait khet");
  };

  // Stage1 implicit diffusion — paddy calibrated 24 steps 10 inject 50 Jacobi
  std::vector<float> hcur(N, 0.0f), rhs(N), eta0(N), etaF(N);
  std::vector<std::vector<float>> depthHist;
  depthHist.reserve(FR_N_STEPS);
  for (int t = 0; t < FR_N_STEPS; ++t) {
    bool inj = (t < FR_N_INJECT);
    for (uint32_t i = 0; i < N; ++i) {
      float hc = (inj && inGrid[i] > 0.5f) ? FR_INFLOW : hcur[i];
      rhs[i] = bot[i] + hc;
      eta0[i] = rhs[i];
    }
    kWrite(dev, bRhs, rhs.data());
    kWrite(dev, bA, eta0.data());
    KPC pc{float(R), float(C), FR_ALPHA, FR_INFLOW, inj ? 1.0f : 0.0f};
    const KBuf *last = &bA;
    for (int k = 0; k < FR_N_JACOBI; ++k) {
      bool even = (k % 2 == 0);
      sweep(even ? setAB : setBA, pc);
      last = even ? &bB : &bA;
    }
    kRead(dev, *last, etaF.data());
    std::vector<float> cur(N);
    for (uint32_t i = 0; i < N; ++i) {
      if (openF[i] <= 0.5f)
        cur[i] = 0.0f;
      else if (inj && inGrid[i] > 0.5f)
        cur[i] = FR_INFLOW;
      else {
        float d = etaF[i] - bot[i];
        cur[i] = d > 0.0f ? d : 0.0f;
      }
    }
    hcur = cur;
    depthHist.push_back(std::move(cur));
  }

  // Stage2 peak momentum — interior argmax (monsoon rises then recedes)
  int tstar = 0;
  double bestM = -1.0;
  for (int t = 0; t < FR_N_STEPS; ++t) {
    double m = khetMomentum(bot, depthHist[t], openF, R, C);
    if (m > bestM) {
      bestM = m;
      tstar = t;
    }
  }
  const std::vector<float> &h = depthHist[tstar];

  // Stage3 Beffa FI tertiled
  std::vector<float> speed(N, 0.0f);
  khetSpeed(bot, h, openF, R, C, speed);
  std::vector<float> fi(N, 0.0f), fiVals;
  fiVals.reserve(N);
  for (uint32_t i = 0; i < N; ++i) {
    if (openF[i] <= 0.5f)
      continue;
    fi[i] = h[i] * std::max(1.0f, speed[i]);
    fiVals.push_back(fi[i]);
  }
  std::sort(fiVals.begin(), fiVals.end());
  float fBound1 = 0.0f, fBound2 = 0.0f;
  int nf = int(fiVals.size());
  if (nf > 0) {
    int i1 = std::min(std::max(int(std::ceil(nf / 3.0)) - 1, 0), nf - 1);
    int i2 = std::min(std::max(int(std::ceil(2.0 * nf / 3.0)) - 1, 0), nf - 1);
    fBound1 = fiVals[i1];
    fBound2 = fiVals[i2];
  }
  std::vector<int> fiLev(N, 0);
  for (uint32_t i = 0; i < N; ++i) {
    if (openF[i] <= 0.5f)
      continue;
    fiLev[i] = (fi[i] < fBound1) ? 1 : ((fi[i] < fBound2) ? 2 : 3);
  }

  // Stage4 evacuation difficulty — paddy costs 2/4/6 at 1.0/1.6m
  const int64_t INF64 = int64_t(1) << 30;
  std::vector<int64_t> dist(N, INF64);
  std::vector<int> wCost(N);
  for (uint32_t i = 0; i < N; ++i)
    wCost[i] = (h[i] < FR_WADE_LOW)
                   ? FR_COST_SHALLOW
                   : ((h[i] < FR_WADE_HIGH) ? FR_COST_MID : FR_COST_DEEP);
  using Q = std::pair<int64_t, int>;
  std::priority_queue<Q, std::vector<Q>, std::greater<Q>> pq;
  for (uint32_t i = 0; i < N; ++i)
    if (exit[i] > 0.5f && openF[i] > 0.5f) {
      dist[i] = 0;
      pq.push({0, int(i)});
    }
  while (!pq.empty()) {
    auto [d, i] = pq.top();
    pq.pop();
    if (d > dist[i])
      continue;
    int r = i / C, c = i % C;
    for (int k = 0; k < 4; ++k) {
      int nr = r + K_DR[k], nc = c + K_DC[k];
      if (nr < 0 || nr >= R || nc < 0 || nc >= C)
        continue;
      int j = nr * C + nc;
      if (openF[j] > 0.5f) {
        int64_t nd = d + wCost[j];
        if (nd < dist[j]) {
          dist[j] = nd;
          pq.push({nd, j});
        }
      }
    }
  }
  std::vector<int64_t> reach;
  for (uint32_t i = 0; i < N; ++i)
    if (openF[i] > 0.5f && dist[i] < INF64)
      reach.push_back(dist[i]);
  std::sort(reach.begin(), reach.end());
  int64_t d1 = 0, d2 = 0;
  int nr = int(reach.size());
  if (nr > 0) {
    int i1 = std::min(std::max(int(std::ceil(nr / 3.0)) - 1, 0), nr - 1);
    int i2 = std::min(std::max(int(std::ceil(2.0 * nr / 3.0)) - 1, 0), nr - 1);
    d1 = reach[i1];
    d2 = reach[i2];
  }

  std::vector<float> out(N, 0.0f);
  for (uint32_t i = 0; i < N; ++i) {
    if (openF[i] <= 0.5f)
      continue;
    int diffL;
    if (dist[i] >= INF64)
      diffL = 3;
    else if (dist[i] < d1)
      diffL = 1;
    else if (dist[i] < d2)
      diffL = 2;
    else
      diffL = 3;
    int risk = fiLev[i] + diffL - 1;
    if (risk < 1)
      risk = 1;
    if (risk > 5)
      risk = 5;
    out[i] = float(risk);
  }

  vkDestroyFence(dev, fence, nullptr);
  vkDestroyCommandPool(dev, cpool, nullptr);
  vkDestroyDescriptorPool(dev, dpool, nullptr);
  vkDestroyPipeline(dev, pipe, nullptr);
  vkDestroyShaderModule(dev, mod, nullptr);
  vkDestroyPipelineLayout(dev, pl, nullptr);
  vkDestroyDescriptorSetLayout(dev, dsl, nullptr);
  for (KBuf *b : {&bBottom, &bOpen, &bInlet, &bRhs, &bA, &bB}) {
    vkDestroyBuffer(dev, b->buf, nullptr);
    vkFreeMemory(dev, b->mem, nullptr);
  }
  vkDestroyDevice(dev, nullptr);
  vkDestroyInstance(inst, nullptr);
  return out;
}
