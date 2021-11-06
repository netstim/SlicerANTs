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
string(REPLACE "RUNTIME_\${ANTS_FUNCTION_NAME}" "RuntimeLibraries"
    cmakefile_src "${cmakefile_src}")
string(REPLACE "RUNTIME_antsUtilities" "RuntimeLibraries"
    cmakefile_src "${cmakefile_src}")
string(REPLACE "DEVELOPMENT_\${ANTS_FUNCTION_NAME}" "DevelopmentLibraries"
    cmakefile_src "${cmakefile_src}")
string(REPLACE "DEVELOPMENT_antsUtilities" "DevelopmentLibraries"
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

#-----------------------------------
# Filter Update

set(cmakefile ${ants_SRC_DIR}/Examples/antsDisplacementAndVelocityFieldRegistrationCommandIterationUpdate.h)
file(READ ${cmakefile} cmakefile_src)
string(FIND "${cmakefile_src}" "std::cout << \"<filter-stage-progress>\"" found_patched)
if ("${found_patched}" LESS 0)
message(STATUS "ants: Patching filter log ${cmakefile}")
string(REPLACE 
    "this->Logger() << \"1DIAGNOSTIC, \""
    "std::cout << \"<filter-stage-progress>\" << (float)lCurrentIteration/(float)this->m_NumberOfIterations[filter->GetCurrentLevel()] << \"</filter-stage-progress>\" << std::endl << std::flush;\nthis->Logger() << \"1DIAGNOSTIC, \""
    cmakefile_src "${cmakefile_src}")
file(WRITE ${cmakefile} "${cmakefile_src}")
else()
message(STATUS "ants: Filter log already patched ${cmakefile}")
endif()

set(cmakefile ${ants_SRC_DIR}/Examples/antsRegistrationOptimizerCommandIterationUpdate.h)
file(READ ${cmakefile} cmakefile_src)
string(FIND "${cmakefile_src}" "std::cout << \"<filter-stage-progress>\"" found_patched)
if ("${found_patched}" LESS 0)
message(STATUS "ants: Patching filter log ${cmakefile}")
string(REPLACE 
    "this->Logger() << \"2DIAGNOSTIC, \""
    "std::cout << \"<filter-stage-progress>\" << (float)currentIteration/(float)lastIteration << \"</filter-stage-progress>\" << std::endl << std::flush;\nthis->Logger() << \"2DIAGNOSTIC, \""
    cmakefile_src "${cmakefile_src}")
file(WRITE ${cmakefile} "${cmakefile_src}")
else()
message(STATUS "ants: Filter log already patched ${cmakefile}")
endif()

set(cmakefile ${ants_SRC_DIR}/Examples/itkantsRegistrationHelper.h)
file(READ ${cmakefile} cmakefile_src)
string(FIND "${cmakefile_src}" "std::cout << \"<filter-comment>\"" found_patched)
if ("${found_patched}" LESS 0)
message(STATUS "ants: Patching filter log ${cmakefile}")
string(REPLACE 
    "this->Logger() << std::endl << \"*** Running \"" 
    "std::cout << \"<filter-comment>\" << currentTransform->GetNameOfClass() << \"</filter-comment>\" << std::endl << std::flush;\nthis->Logger() << std::endl << \"*** Running \""
    cmakefile_src "${cmakefile_src}")
file(WRITE ${cmakefile} "${cmakefile_src}")
else()
message(STATUS "ants: Filter log already patched ${cmakefile}")
endif()

set(cmakefile ${ants_SRC_DIR}/Examples/itkantsRegistrationHelper.hxx)
file(READ ${cmakefile} cmakefile_src)
string(FIND "${cmakefile_src}" "std::cout << \"<filter-comment>\"" found_patched)
if ("${found_patched}" LESS 0)
message(STATUS "ants: Patching filter log ${cmakefile}")
string(REGEX REPLACE 
    "this->Logger([^\\;]+Running )([^\\*\\;]+)" 
    "std::cout << \"<filter-comment>\" << \"\\2\" << \"</filter-comment>\" << std::endl << std::flush;\nthis->Logger\\1\\2"
    cmakefile_src "${cmakefile_src}")
string(REPLACE 
    "this->Logger() << std::endl << \"Stage \"" 
    "std::cout << \"<filter-progress>\" << (float)(currentStageNumber+1)/(float)(this->m_NumberOfStages+1) << \"</filter-progress>\" << std::endl << std::flush;\nthis->Logger() << std::endl << \"Stage \""
    cmakefile_src "${cmakefile_src}")
file(WRITE ${cmakefile} "${cmakefile_src}")
else()
message(STATUS "ants: Filter log already patched ${cmakefile}")
endif()