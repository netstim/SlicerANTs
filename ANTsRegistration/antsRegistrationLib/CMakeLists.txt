set(ANTS_LIB_PYTHON_SCRIPTS
  util.py
  Widgets/delegates.py
  Widgets/tables.py
  )

set(ANTS_LIB_PYTHON_RESOURCES
  __init__.py
  Widgets/__init__.py
  )

ctkMacroCompilePythonScript(
  TARGET_NAME antsRegistrationLib
  SCRIPTS "${ANTS_LIB_PYTHON_SCRIPTS}"
  RESOURCES "${ANTS_LIB_PYTHON_RESOURCES}"
  DESTINATION_DIR ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}${_destination_subdir}/antsRegistrationLib
  INSTALL_DIR ${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}/antsRegistrationLib
  NO_INSTALL_SUBDIR
  )