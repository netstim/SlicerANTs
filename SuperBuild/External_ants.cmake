
set(proj ants)

# Set dependency list
set(${proj}_DEPENDS
  ""
  )
  if(DEFINED Slicer_SOURCE_DIR)
  list(APPEND ${proj}_DEPENDS
    ITK
    )
endif()

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj)

if(${SUPERBUILD_TOPLEVEL_PROJECT}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${SUPERBUILD_TOPLEVEL_PROJECT}_USE_SYSTEM_${proj} is not supported !")
endif()

# Sanity checks
if(DEFINED ants_DIR AND NOT EXISTS ${ants_DIR})
  message(FATAL_ERROR "ants_DIR [${ants_DIR}] variable is defined but corresponds to nonexistent directory")
endif()

if(NOT DEFINED ${proj}_DIR AND NOT ${SUPERBUILD_TOPLEVEL_PROJECT}_USE_SYSTEM_${proj})

  ExternalProject_SetIfNotDefined(
   ${SUPERBUILD_TOPLEVEL_PROJECT}_${proj}_GIT_REPOSITORY
   "${EP_GIT_PROTOCOL}://github.com/ANTsX/ANTs.git"
   QUIET
   )

  ExternalProject_SetIfNotDefined(
   ${SUPERBUILD_TOPLEVEL_PROJECT}_${proj}_GIT_TAG
   "8c4e2077f43e92f2134fa578ee62ccd8f51162ef" # 2024.09.10
   QUIET
   )

  set(EP_SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj})
  set(EP_BINARY_DIR ${CMAKE_BINARY_DIR}/${proj}-build)

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    GIT_REPOSITORY "${${SUPERBUILD_TOPLEVEL_PROJECT}_${proj}_GIT_REPOSITORY}"
    GIT_TAG "${${SUPERBUILD_TOPLEVEL_PROJECT}_${proj}_GIT_TAG}"
    SOURCE_DIR ${EP_SOURCE_DIR}
    BINARY_DIR ${EP_BINARY_DIR}
    PATCH_COMMAND ${CMAKE_COMMAND} -Dants_SRC_DIR=${CMAKE_BINARY_DIR}/${proj}
      -P ${CMAKE_CURRENT_LIST_DIR}/${proj}_patch.cmake
    CMAKE_CACHE_ARGS
      # Compiler settings
      -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_CXX_STANDARD:STRING=${CMAKE_CXX_STANDARD}
      -DCMAKE_CXX_STANDARD_REQUIRED:BOOL=${CMAKE_CXX_STANDARD_REQUIRED}
      -DCMAKE_CXX_EXTENSIONS:BOOL=${CMAKE_CXX_EXTENSIONS}
      -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
      # Output directories
      -DCMAKE_RUNTIME_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${Slicer_THIRDPARTY_BIN_DIR}
      -DCMAKE_LIBRARY_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${Slicer_THIRDPARTY_LIB_DIR}
      -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}
      -DCMAKE_INSTALL_LIBDIR:STRING=${Slicer_INSTALL_THIRDPARTY_LIB_DIR}
      -DCMAKE_INSTALL_BINDIR:STRING=${Slicer_INSTALL_THIRDPARTY_LIB_DIR}
      # ZLIB
      -DZLIB_LIBRARY:PATH=${ZLIB_LIBRARY}
      -DZLIB_INCLUDE_DIR:PATH=${ZLIB_INCLUDE_DIR}
      # ITK
      -DUSE_SYSTEM_ITK:BOOL=ON
      -DITK_DIR:PATH=${ITK_DIR}
      # VTK
      -DUSE_VTK:BOOL=OFF
      # Options
      -DBUILD_ALL_ANTS_APPS:BOOL=OFF
      -DBUILD_TESTING:BOOL=OFF
      -DBUILD_SHARED_LIBS:BOOL=ON
      -DANTS_INSTALL_LIBS_ONLY:BOOL=OFF
      # Dependencies
    INSTALL_COMMAND ""
    DEPENDS
      ${${proj}_DEPENDS}
    )

  ExternalProject_GenerateProjectDescription_Step(${proj})

  set(${proj}_DIR ${EP_BINARY_DIR}/ANTS-build)

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDS})
endif()

mark_as_superbuild(${proj}_DIR:PATH)
