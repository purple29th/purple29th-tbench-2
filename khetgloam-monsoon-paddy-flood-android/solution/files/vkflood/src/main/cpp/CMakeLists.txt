cmake_minimum_required(VERSION 3.22.1)
project(vkflood LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Raw Vulkan (no Kompute): the Android NDK ships the Vulkan loader + headers, so
# the arm64 lib links libvulkan directly.
add_library(vkflood SHARED native-lib.cpp flood_risk.cpp)
target_include_directories(vkflood PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

find_library(vulkan-lib vulkan)
find_library(log-lib log)
target_link_libraries(vkflood PRIVATE ${vulkan-lib} ${log-lib})
