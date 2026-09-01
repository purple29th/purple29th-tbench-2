cmake_minimum_required(VERSION 3.20)
project(vkflood_host LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Raw Vulkan (no Kompute): link the system Vulkan loader; the .so runs on lavapipe.
find_package(Vulkan REQUIRED)

set(CPP ${CMAKE_SOURCE_DIR}/../vkflood/src/main/cpp)
add_library(vkflood_host SHARED ${CPP}/native-lib.cpp ${CPP}/flood_risk.cpp)
# JNI headers only (the JVM supplies the symbols at runtime); avoid find_package(JNI)
# which requires AWT and fails on a headless JDK.
target_include_directories(vkflood_host PRIVATE
    ${CPP}
    $ENV{JAVA_HOME}/include
    $ENV{JAVA_HOME}/include/linux)
target_link_libraries(vkflood_host PRIVATE Vulkan::Vulkan)
