import qt, slicer

class ComboDelegate(qt.QItemDelegate):
  def __init__(self, parent, antsType, setSettingsFormatFunction):
    qt.QItemDelegate.__init__(self, parent)
    self.antsType = antsType
    self.setSettingsFormatFunction = setSettingsFormatFunction

  def createEditor(self, parent, option, index):
    combo = qt.QComboBox(parent)
    combo.addItems(self.antsType.getSubClassesNames())
    combo.currentTextChanged.connect(lambda text: self.setSettingsFormatFunction(text))
    return combo

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.setCurrentText(index.model().data(index))
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.currentText, qt.Qt.DisplayRole)
    model.setData(index, self.antsType.getSubClassByName(editor.currentText).details, qt.Qt.ToolTipRole)

class TextEditDelegate(qt.QItemDelegate):
  def __init__(self, parent, antsType):
    qt.QItemDelegate.__init__(self, parent)
    self.antsType = antsType

  def createEditor(self, parent, option, index):
    lineEdit = qt.QLineEdit(parent)
    return lineEdit

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.text = index.model().data(index) if index.model().data(index) else self.getDefaultSettings(index)
    editor.blockSignals(False)
  
  def getDefaultSettings(self, index):
    name = index.model().data(index.siblingAtColumn(0))
    return self.antsType.getSubClassByName(name).settingsDefault

  def setModelData(self, editor, model, index):
    model.setData(index, editor.text)


class MRMLComboDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    metricType = index.model().data(index.siblingAtColumn(0))
    if metricType in ['ICP', 'PSE', 'JHCT']:
      nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    else:
      nodeTypes = ["vtkMRMLScalarVolumeNode", "vtkMRMLLabelMapVolumeNode"]
    combo = slicer.qMRMLNodeComboBox(parent)
    combo.setEnabled(True)
    combo.nodeTypes = nodeTypes
    combo.addEnabled = False
    combo.noneEnabled = True
    combo.removeEnabled = False
    combo.setMRMLScene(slicer.mrmlScene)
    return combo

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.setCurrentNodeID(index.model().data(index, qt.Qt.UserRole))
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    currentNode = editor.currentNode()
    currentNodeName = currentNode.GetName() if currentNode else ''
    currentNodeID = currentNode.GetID() if currentNode else ''
    model.setData(index, currentNodeName, qt.Qt.DisplayRole)
    model.setData(index, currentNodeID, qt.Qt.UserRole)


class SpinBoxDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    spinBox = qt.QSpinBox(parent)
    spinBox.setSingleStep(1)
    spinBox.maximum = 1e4
    return spinBox

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.value = index.model().data(index) if index.model().data(index) else 0
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.value)
