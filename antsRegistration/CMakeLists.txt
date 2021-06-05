#-----------------------------------------------------------------------------
set(MODULE_NAME antsRegistration)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  antsRegistrationLib/Widgets/__init__.py
  antsRegistrationLib/Widgets/delegates.py
  antsRegistrationLib/Widgets/tables.py
  antsRegistrationLib/__init__.py
  antsRegistrationLib/util.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  )

set(REGISTRATION_PRESET_FILES
  Rigid
  Rigid+Affine
  QuickSyN
  )

foreach (presetfile ${REGISTRATION_PRESET_FILES})
  set(MODULE_PYTHON_RESOURCES ${MODULE_PYTHON_RESOURCES} "Resources/Presets/${presetfile}.json")
endforeach()

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
