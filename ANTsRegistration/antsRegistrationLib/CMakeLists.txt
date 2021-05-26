set(ANTS_LIB_PYTHON_SCRIPTS
  metrics.py
  transforms.py
  )

ctkMacroCompilePythonScript(
  TARGET_NAME antsRegistrationLib
  SCRIPTS "${ANTS_LIB_PYTHON_SCRIPTS}"
  RESOURCES __init__.py
  DESTINATION_DIR ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}${_destination_subdir}/antsRegistrationLib
  INSTALL_DIR ${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}/antsRegistrationLib
  NO_INSTALL_SUBDIR
  )