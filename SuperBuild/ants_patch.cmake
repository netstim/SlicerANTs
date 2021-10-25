# Set which ANTs apps to compile

set(build_ants_apps
  antsRegistration
  antsApplyTransforms
)

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
file(WRITE ${cmakefile} "${cmakefile_src}")
else()
message(STATUS "ants: Already patched ${cmakefile}")
endif()
