# Set which ANTs apps to compile

set(build_ants_apps
  antsRegistration
  antsApplyTransforms
)

file(COPY ${CMAKE_CURRENT_LIST_DIR}/antsConfig.cmake DESTINATION ${ants_SRC_DIR}/Examples/)

set(cmakefile
  ${ants_SRC_DIR}/Examples/CMakeLists.txt
)

file(READ ${cmakefile} cmakefile_src)
string(FIND "${cmakefile_src}" "CORE_ANTS_APPS ${build_ants_apps}" found_patched)
if ("${found_patched}" LESS 0)
message(STATUS "ants: Patching ${cmakefile}")
string(REGEX REPLACE "\\(CORE_ANTS_APPS[^\\)]+" "\(CORE_ANTS_APPS ${build_ants_apps}"
    cmakefile_src "${cmakefile_src}")
string(REGEX REPLACE "\\(MORE_ANTS_APPS[^\\)]+" "\(MORE_ANTS_APPS "
    cmakefile_src "${cmakefile_src}")
string(REPLACE "install(TARGETS antsUtilities" "install(TARGETS antsUtilities EXPORT antsTargets"
    cmakefile_src "${cmakefile_src}")
string(REPLACE "install(TARGETS l_\${ANTS_FUNCTION_NAME} \${ANTS_FUNCTION_NAME}" "install(TARGETS l_\${ANTS_FUNCTION_NAME} \${ANTS_FUNCTION_NAME} EXPORT antsTargets"
    cmakefile_src "${cmakefile_src}")
string(REPLACE "\${\${PROJECT_NAME}_VERSION}" "\${\${PROJECT_NAME}_VERSION_MAJOR}"
    cmakefile_src "${cmakefile_src}")
string(APPEND cmakefile_src
"
include(CMakePackageConfigHelpers)
write_basic_package_version_file(
  \"\${CMAKE_CURRENT_BINARY_DIR}/../antsConfigVersion.cmake\"
  VERSION 0.1
  COMPATIBILITY AnyNewerVersion
)

export(EXPORT antsTargets
  FILE \"\${CMAKE_CURRENT_BINARY_DIR}/../antsTargets.cmake\"
  NAMESPACE Upstream::
)
configure_file(antsConfig.cmake
  \"\${CMAKE_CURRENT_BINARY_DIR}/../antsConfig.cmake\"
  COPYONLY
)
"
)
file(WRITE ${cmakefile} "${cmakefile_src}")
else()
message(STATUS "ants: Already patched ${cmakefile}")
endif()
