cmake_minimum_required(VERSION 3.16)
project(pathfinder)

set(CMAKE_CXX_FLAGS "-std=c++17")
set(CMAKE_CXX_COMPILER g++-9)
set(EXECUTABLE_OUTPUT_PATH build)
set(LIBRARY_OUTPUT_PATH build)

include_directories(../core/include)

add_library(fst SHARED ../core/src/fst.cpp)

add_executable(core ../core/src/fast.cpp)
add_executable(test tests/test.cpp)

target_link_libraries(core PRIVATE fst)
target_link_libraries(test PRIVATE fst)