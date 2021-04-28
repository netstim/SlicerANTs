ctkMacroCompilePythonScript(
  TARGET_NAME util
  SCRIPTS util
  RESOURCES __init__.py
  DESTINATION_DIR ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}${_destination_subdir}/Widgets
  INSTALL_DIR ${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}/Widgets
  NO_INSTALL_SUBDIR
  )