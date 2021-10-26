
#-----------------------------------------------------------------------------
set(MODULE_NAME antsApplyTransformsCLI)

#-----------------------------------------------------------------------------

#
# SlicerExecutionModel
#
find_package(SlicerExecutionModel REQUIRED)
include(${SlicerExecutionModel_USE_FILE})

#
# ANTs
#
find_package(ants REQUIRED)

#-----------------------------------------------------------------------------
set(MODULE_INCLUDE_DIRECTORIES
  ${ants_DIR}/../../ants/Examples/include
  )

set(MODULE_SRCS
  )

set(MODULE_TARGET_LIBRARIES
  Upstream::antsUtilities  
  Upstream::l_antsApplyTransforms
  ${ITK_LIBRARIES}
  )

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  TARGET_LIBRARIES ${MODULE_TARGET_LIBRARIES}
  INCLUDE_DIRECTORIES ${MODULE_INCLUDE_DIRECTORIES}
  ADDITIONAL_SRCS ${MODULE_SRCS}
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
