cmake_minimum_required(VERSION 3.18)

project(codebase_copilot_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(pybind11 CONFIG REQUIRED)

set(PYTHON_PACKAGE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../python/codebase_copilot")

pybind11_add_module(_vector_index
    src/binding.cpp
    src/vector_index.cpp
)

target_include_directories(_vector_index PRIVATE include)

if(MSVC)
    target_compile_options(_vector_index PRIVATE /W4)
else()
    target_compile_options(_vector_index PRIVATE -Wall -Wextra -Wpedantic)
endif()

set_target_properties(_vector_index PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${PYTHON_PACKAGE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${PYTHON_PACKAGE_DIR}"
)

foreach(CONFIG_TYPE ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER "${CONFIG_TYPE}" CONFIG_TYPE_UPPER)
    set_target_properties(_vector_index PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY_${CONFIG_TYPE_UPPER} "${PYTHON_PACKAGE_DIR}"
        RUNTIME_OUTPUT_DIRECTORY_${CONFIG_TYPE_UPPER} "${PYTHON_PACKAGE_DIR}"
    )
endforeach()

