// Khetgloam JNI bridge — com.example.vkflood.FloodRisk.floodRisk
// Kerala paddy terrace edition: bund=wall, breach=inlet, footpath=exit
// Implementation in flood_risk.cpp (paddy calibrated
// 24/10/0.25/2.8/12/1.0/1.6/2/4/6) Works static or instance (second arg
// ignored) — OUSB tablet AAR.

#include <jni.h>

#include <vector>

#include "flood_risk.hpp"

extern "C" JNIEXPORT jfloatArray JNICALL
Java_com_example_vkflood_FloodRisk_floodRisk(
    JNIEnv *env, jobject /*self_or_class*/, jfloatArray bottom,
    jfloatArray wall, jfloatArray inlet, jfloatArray exit, jint rows,
    jint cols) {
  jsize n = env->GetArrayLength(bottom);
  std::vector<float> bb(static_cast<size_t>(n));
  std::vector<float> ww(static_cast<size_t>(n));
  std::vector<float> ii(static_cast<size_t>(n));
  std::vector<float> ee(static_cast<size_t>(n));
  env->GetFloatArrayRegion(bottom, 0, n, bb.data());
  env->GetFloatArrayRegion(wall, 0, n, ww.data());
  env->GetFloatArrayRegion(inlet, 0, n, ii.data());
  env->GetFloatArrayRegion(exit, 0, n, ee.data());
  std::vector<float> out =
      floodRisk(bb.data(), ww.data(), ii.data(), ee.data(),
                static_cast<uint32_t>(rows), static_cast<uint32_t>(cols));
  jfloatArray res = env->NewFloatArray(static_cast<jsize>(out.size()));
  env->SetFloatArrayRegion(res, 0, static_cast<jsize>(out.size()), out.data());
  return res;
}
