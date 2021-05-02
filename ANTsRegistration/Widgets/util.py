import qt, ctk

#
# Delegates
#

class ComboDelegate(qt.QItemDelegate):
  def __init__(self, parentWidget):
    self.parentWidget = parentWidget
    qt.QItemDelegate.__init__(self, self.parentWidget.model)

  def createEditor(self, parent, option, index):
    combo = qt.QComboBox(parent)
    combo.addItems(list(self.parentWidget.NameInfoDictionary.keys()))
    combo.currentTextChanged.connect(self.onCurrentTextChanged)
    return combo

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.setCurrentText(index.model().data(index))
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.currentText)

  def onCurrentTextChanged(self, text):
    self.parentWidget.updateSettingsFormatTextFromKey(text)


class SpinBoxDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    spinBox = qt.QDoubleSpinBox(parent)
    spinBox.setSingleStep(0.1)
    return spinBox

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.value = index.model().data(index) if index.model().data(index) else 0
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.value)


class TextEditDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    textEdit = qt.QPlainTextEdit(parent)
    textEdit.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    textEdit.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    textEdit.setLineWrapMode(textEdit.NoWrap)
    return textEdit

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.plainText = index.model().data(index) if index.model().data(index) else ''
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.plainText)


#
# Tables
#

class CustomTable(qt.QWidget):

  RowHeight = 25

  def __init__(self, columnNames):
    super().__init__()
    self.NameInfoDictionary = None

    self.addButton = qt.QPushButton('+')
    self.addButton.clicked.connect(self.onAddButton)

    self.removeButton = qt.QPushButton('-')
    self.removeButton.clicked.connect(self.onRemoveButton)

    self.model = qt.QStandardItemModel(0, len(columnNames))
    for i, columnName in enumerate(columnNames):
      self.model.setHeaderData(i, qt.Qt.Horizontal, columnName)

    self.view = qt.QTableView()
    self.view.setEditTriggers(self.view.CurrentChanged + self.view.DoubleClicked + self.view.SelectedClicked)
    self.view.setSelectionMode(self.view.SingleSelection)
    self.view.setSelectionBehavior(self.view.SelectRows)
    self.view.horizontalHeader().setStretchLastSection(True)
    self.view.setHorizontalScrollMode(self.view.ScrollPerPixel)
    self.view.verticalHeader().setMaximumSectionSize(self.RowHeight)
    self.view.verticalHeader().setMinimumSectionSize(self.RowHeight)
    self.view.verticalHeader().setDefaultSectionSize(self.RowHeight)
    self.view.setFixedHeight(40)
    self.view.setModel(self.model)

    self.view.selectionModel().selectionChanged.connect(self.onSelectionChanged)

    layout = qt.QGridLayout(self)
    layout.addWidget(self.addButton,0,0,1,1)
    layout.addWidget(self.removeButton,0,1,1,1)
    layout.addWidget(self.view,1,0,1,2)

    return layout
  
  def onAddButton(self):
    self.model.insertRow(self.model.rowCount(qt.QModelIndex()))
    self.view.setFixedHeight(self.view.height+self.RowHeight)
  
  def onRemoveButton(self):
    selectedRows = self.view.selectionModel().selectedRows()
    for selectedRow in selectedRows:
      self.model.removeRow(selectedRow.row())
      self.view.setFixedHeight(self.view.height-self.RowHeight)

  def onSelectionChanged(self, selection):
    pass


class TableWithSettings(CustomTable):
  def __init__(self, columnNames):
    layout = CustomTable.__init__(self, columnNames)

    self.settingsFormatText = ctk.ctkFittedTextBrowser()
    self.settingsFormatText.setText('Settings Format: ')
    layout.addWidget(self.settingsFormatText,2,0,1,2)

    self.view.setItemDelegateForColumn(0, ComboDelegate(self))
    self.view.setItemDelegateForColumn(self.model.columnCount()-1, TextEditDelegate(self.model))

  def onAddButton(self):
    super().onAddButton()
    index = self.model.index(self.model.rowCount()-1, 0)
    self.model.setData(index, list(self.NameInfoDictionary.keys())[0])

  def onSelectionChanged(self, selection):
    super().onSelectionChanged(selection)
    indexes = selection.indexes()
    if indexes:
      key = self.model.data(indexes[0].siblingAtColumn(0))
      self.updateSettingsFormatTextFromKey(key)

  def updateSettingsFormatTextFromKey(self, key):
    self.settingsFormatText.setText('Settings Format: ' + self.NameInfoDictionary[key])


class StagesTable(TableWithSettings):
  def __init__(self):
    columnNames = ['Transform', 'Settings']
    TableWithSettings.__init__(self, columnNames)

    self.NameInfoDictionary = {\
      'Rigid': 'gradientStep',\
      'Affine': 'gradientStep',\
      'CompositeAffine': 'gradientStep',\
      'Similarity': 'gradientStep',\
      'Translation': 'gradientStep',\
      'BSpline': 'gradientStep, meshSizeAtBaseLevel',\
      'GaussianDisplacementField': 'gradientStep, updateFieldVarianceInVoxelSpace, totalFieldVarianceInVoxelSpace',\
      'BSplineDisplacementField': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <totalFieldMeshSizeAtBaseLevel=0>, <splineOrder=3>',\
      'TimeVaryingVelocityField': 'gradientStep, numberOfTimeIndices, updateFieldVarianceInVoxelSpace, updateFieldTimeVariance, totalFieldVarianceInVoxelSpace, totalFieldTimeVariance',\
      'TimeVaryingBSplineVelocityField': 'gradientStep, velocityFieldMeshSize, <numberOfTimePointSamples=4>, <splineOrder=3>',\
      'SyN': 'gradientStep, <updateFieldVarianceInVoxelSpace= 3>, <totalFieldVarianceInVoxelSpace=0>',\
      'BSplineSyN': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <totalFieldMeshSizeAtBaseLevel=0>, <splineOrder=3>',\
      'Exponential': 'gradientStep, updateFieldVarianceInVoxelSpace, velocityFieldVarianceInVoxelSpace, <numberOfIntegrationSteps>',\
      'BSplineExponential': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <velocityFieldMeshSizeAtBaseLevel=0>, <numberOfIntegrationSteps>, <splineOrder=3>'\
    }

class MetricsTable(TableWithSettings):
  def __init__(self):
    columnNames = ['Type', 'Fixed', 'Moving', 'Settings']
    TableWithSettings.__init__(self, columnNames)

    self.NameInfoDictionary = {\
      'CC': 'metricWeight, radius, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
      'MI': 'metricWeight, numberOfBins, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
      'Mattes': 'metricWeight, numberOfBins, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
      'MeanSquares': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
      'Demons': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
      'GC': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
      'ICP': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>',\
      'PSE': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>,<pointSetSigma=1>, <kNeighborhood=50>',\
      'JHCT': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>, <pointSetSigma=1>, <kNeighborhood=50>, <alpha=1.1>, <useAnisotropicCovariances=1>',\
      'IGDM': 'metricWeight, fixedMask, movingMask, <neighborhoodRadius=0x0>, <intensitySigma=0>, <distanceSigma=0>, <kNeighborhood=1>, <gradientSigma=1>',\
    }


class LevelsTable(CustomTable):

  def __init__(self):
    columnNames = ['Convergence', 'Smoothing Sigmas', 'Shrink Factors']
    CustomTable.__init__(self, columnNames)

    self.view.setItemDelegateForColumn(0, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(1, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(2, SpinBoxDelegate(self.model))

