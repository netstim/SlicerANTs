import qt, ctk, slicer

#
# Delegates
#

class ComboDelegate(qt.QItemDelegate):
  def __init__(self, parent, nameInfoDictionary, settingsFormatText):
    qt.QItemDelegate.__init__(self, parent)
    self.nameInfoDictionary = nameInfoDictionary
    self.settingsFormatText = settingsFormatText

  def createEditor(self, parent, option, index):
    combo = qt.QComboBox(parent)
    combo.addItems(list(self.nameInfoDictionary.keys()))
    combo.currentTextChanged.connect(self.onCurrentTextChanged)
    return combo

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.setCurrentText(index.model().data(index))
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.currentText, qt.Qt.DisplayRole)
    model.setData(index, self.nameInfoDictionary[editor.currentText]['Details'], qt.Qt.ToolTipRole)

  def onCurrentTextChanged(self, key):
    self.settingsFormatText.setText('Settings Format: ' + self.nameInfoDictionary[key]['Format'])


class TextEditDelegate(qt.QItemDelegate):
  def __init__(self, parent, nameInfoDictionary):
    qt.QItemDelegate.__init__(self, parent)
    self.nameInfoDictionary = nameInfoDictionary

  def createEditor(self, parent, option, index):
    textEdit = qt.QPlainTextEdit(parent)
    textEdit.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    textEdit.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    textEdit.setLineWrapMode(textEdit.NoWrap)
    return textEdit

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.plainText = index.model().data(index) if index.model().data(index) else self.getDefaultSettings(index)
    editor.blockSignals(False)
  
  def getDefaultSettings(self, index):
    key = index.model().data(index.siblingAtColumn(0))
    return self.nameInfoDictionary[key]['Default']

  def setModelData(self, editor, model, index):
    model.setData(index, editor.plainText.replace('\n',''))


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




#
# Tables
#

class CustomTable(qt.QWidget):

  RowHeight = 25

  def __init__(self, columnNames):
    super().__init__()

    self.addButton = qt.QPushButton('+')
    self.addButton.clicked.connect(self.onAddButton)

    self.removeButton = qt.QPushButton('-')
    self.removeButton.clicked.connect(self.onRemoveButton)

    buttonsFrame = qt.QFrame()
    buttonsFrame.setLayout(qt.QHBoxLayout())
    buttonsFrame.layout().addWidget(self.addButton)
    buttonsFrame.layout().addWidget(self.removeButton)

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

    layout = qt.QVBoxLayout(self)
    layout.addWidget(buttonsFrame)
    layout.addWidget(self.view)

    return layout
  
  def onAddButton(self):
    self.model.insertRow(self.model.rowCount())
    self.view.setFixedHeight(self.view.height+self.RowHeight)
    if self.model.rowCount() == 1:
      self.setDefaultFirstRow()
    else:
      self.setDefaultNthRow(self.model.rowCount()-1)

  def onRemoveButton(self):
    if self.model.rowCount() == 1:
      return
    else:
      self.removeSelectedRow()
  
  def removeSelectedRow(self):
    selectedRow = self.getSelectedRow()
    if selectedRow:
      self.model.removeRow(selectedRow)
      self.view.setFixedHeight(self.view.height-self.RowHeight)

  def getSelectedRow(self):
    selectedRows = self.view.selectionModel().selectedRows()
    for selectedRow in selectedRows:
      return selectedRow.row() # is a single selection view

  def onSelectionChanged(self, selection):
    pass

  def getParametersFromGUI(self):
    parameters = []
    for i in range(self.model.rowCount()):
      parameters.append(self.getNthRowParametersFromGUI(i))
    return parameters

  def getNthRowParametersFromGUI(self, N):
    parameters = {}
    for col in range(self.model.columnCount()):
      index = self.model.index(N, col)
      itemData = self.model.itemData(index)
      if qt.Qt.UserRole in itemData.keys():
        data = itemData[qt.Qt.UserRole]
      elif qt.Qt.DisplayRole in itemData.keys():
        data = itemData[qt.Qt.DisplayRole]
      else:
        data = ''
      parameters[self.model.headerData(col, qt.Qt.Horizontal)] = data
    return parameters

  def setGUIFromParameters(self, parameters):
    self.model.clear()
    for N,params in enumerate(parameters):
      self.model.insertRow(self.model.rowCount())
      self.setNthRowGUIFromParameters(N, params)

  def setNthRowGUIFromParameters(self, N, parameters):
    for col,val in enumerate(parameters.values()):
      index = self.model.index(N, col)
      self.model.setData(index, val)

class TableWithSettings(CustomTable):
  def __init__(self, columnNames):
    layout = CustomTable.__init__(self, columnNames)

    self.settingsFormatText = ctk.ctkFittedTextBrowser()
    self.settingsFormatText.setText('Settings Format: ')
    layout.addWidget(self.settingsFormatText)

    self.view.setItemDelegateForColumn(0, ComboDelegate(self.model, self.nameInfoDictionary, self.settingsFormatText))
    self.view.setItemDelegateForColumn(self.model.columnCount()-1, TextEditDelegate(self.model, self.nameInfoDictionary))

  def onSelectionChanged(self, selection):
    super().onSelectionChanged(selection)
    indexes = selection.indexes()
    if indexes:
      key = self.model.data(indexes[0].siblingAtColumn(0))
      self.settingsFormatText.setText('Settings Format: ' + self.nameInfoDictionary[key]['Format'])


class StagesTable(TableWithSettings):
  def __init__(self):
    columnNames = ['Transform', 'Settings']
    self.nameInfoDictionary = TransformsNameInfo
    TableWithSettings.__init__(self, columnNames)

    self.settingsFormatText.setToolTip("The gradientStep or learningRate characterizes the gradient descent optimization and is scaled appropriately for each transform using the shift scales estimator. Subsequent parameters are transform-specific and can be determined from the usage. For the B-spline transforms one can also specify the smoothing in terms of spline distance (i.e. knot spacing).")

  def setDefaultFirstRow(self):
    index = self.model.index(0, 0)
    self.model.setData(index, 'Rigid')

  def setDefaultNthRow(self, N):
    index = self.model.index(N, 0)
    aboveData =  self.model.data(index.siblingAtRow(N-1))
    if aboveData == 'Rigid':
      newData = 'Affine'
    elif aboveData == 'Affine':
      newData = 'SyN'
    else:
      newData = 'SyN'
    self.model.setData(index, newData)
  
class MetricsTable(TableWithSettings):
  def __init__(self):
    columnNames = ['Type', 'Fixed', 'Moving', 'Settings']
    self.nameInfoDictionary = MetricsNameInfo
    TableWithSettings.__init__(self, columnNames)

    self.settingsFormatText.setToolTip(" The 'metricWeight' variable is used to modulate the per stage weighting of the metrics. The metrics can also employ a sampling strategy defined by a sampling percentage. The sampling strategy defaults to 'None' (aka a dense sampling of one sample per voxel), otherwise it defines a point set over which to optimize the metric. The point set can be on a regular lattice or a random lattice of points slightly perturbed to minimize aliasing artifacts. samplingPercentage defines the fraction of points to select from the domain.")

    self.view.setItemDelegateForColumn(1, MRMLComboDelegate(self.model))
    self.view.setItemDelegateForColumn(2, MRMLComboDelegate(self.model))

  def setDefaultFirstRow(self):
    self.setDefaultNthRow(0)

  def setDefaultNthRow(self, N):
    index = self.model.index(N, 0)
    self.model.setData(index, 'MI')

class LevelsTable(CustomTable):

  def __init__(self):
    columnNames = ['Convergence', 'Smoothing Sigmas', 'Shrink Factors']
    layout = CustomTable.__init__(self, columnNames)

    self.view.setItemDelegateForColumn(0, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(1, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(2, SpinBoxDelegate(self.model))

    self.smoothingSigmasUnitComboBox = qt.QComboBox()
    self.smoothingSigmasUnitComboBox.addItems(['vox', 'mm'])

    self.convergenceThresholdSpinBox = qt.QSpinBox()
    self.convergenceThresholdSpinBox.value = 6

    self.convergenceWindowSizeSpinBox = qt.QSpinBox()
    self.convergenceWindowSizeSpinBox.value = 10

    levelsSettingsFrame = qt.QFrame()
    levelsSettingsFrame.setLayout(qt.QFormLayout())
    levelsSettingsFrame.layout().addRow('Smoothing Sigmas Unit: ', self.smoothingSigmasUnitComboBox)
    levelsSettingsFrame.layout().addRow('Convergence Threshold (1e-N): ', self.convergenceThresholdSpinBox)
    levelsSettingsFrame.layout().addRow('Convergence Window Size: ', self.convergenceWindowSizeSpinBox)

    layout.addWidget(levelsSettingsFrame)

  def setDefaultFirstRow(self):
    defaults = [1000, 4, 8]
    for i,d in enumerate(defaults):
      index = self.model.index(0, i)
      self.model.setData(index, d)

  def setDefaultNthRow(self, N):
    for column in range(3):
      index = self.model.index(N, column)
      aboveIndex =  index.siblingAtRow(N-1)
      newData = max(1, round(self.model.data(aboveIndex) * 0.5))
      self.model.setData(index, newData)


TransformsNameInfo = {\
  'Rigid': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': '0.1'},\
  'Affine': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'CompositeAffine': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'Similarity': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'Translation': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'BSpline': {\
    'Details': '',\
    'Format': 'gradientStep, meshSizeAtBaseLevel',\
    'Default': ''},\
  'GaussianDisplacementField': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldVarianceInVoxelSpace, totalFieldVarianceInVoxelSpace',\
    'Default': ''},\
  'BSplineDisplacementField': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <totalFieldMeshSizeAtBaseLevel=0>, <splineOrder=3>',\
    'Default': ''},\
  'TimeVaryingVelocityField': {\
    'Details': '',\
    'Format': 'gradientStep, numberOfTimeIndices, updateFieldVarianceInVoxelSpace, updateFieldTimeVariance, totalFieldVarianceInVoxelSpace, totalFieldTimeVariance',\
    'Default': ''},\
  'TimeVaryingBSplineVelocityField': {\
    'Details': '',\
    'Format': 'gradientStep, velocityFieldMeshSize, <numberOfTimePointSamples=4>, <splineOrder=3>',\
    'Default': ''},\
  'SyN': {\
    'Details': '',\
    'Format': 'gradientStep, <updateFieldVarianceInVoxelSpace= 3>, <totalFieldVarianceInVoxelSpace=0>',\
    'Default': ''},\
  'BSplineSyN': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <totalFieldMeshSizeAtBaseLevel=0>, <splineOrder=3>',\
    'Default': ''},\
  'Exponential': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldVarianceInVoxelSpace, velocityFieldVarianceInVoxelSpace, <numberOfIntegrationSteps>',\
    'Default': ''},\
  'BSplineExponential': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <velocityFieldMeshSizeAtBaseLevel=0>, <numberOfIntegrationSteps>, <splineOrder=3>',\
    'Default': ''}\
}

MetricsNameInfo = {\
  'CC': {\
    'Details': 'ANTS neighborhood cross correlation',\
    'Format': 'metricWeight, radius, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'MI': {\
    'Details': 'Mutual Information',\
    'Format': 'metricWeight, numberOfBins, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'Mattes': {\
    'Details': '',\
    'Format': 'metricWeight, numberOfBins, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'MeanSquares': {\
    'Details': '',\
    'Format': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'Demons': {\
    'Details': '',\
    'Format': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'GC': {\
    'Details': 'Global Correlation',\
    'Format': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'ICP': {\
    'Details': 'Euclidean',\
    'Format': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>',\
    'Default': ''},\
  'PSE': {\
    'Details': 'Point-set expectation',\
    'Format': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>,<pointSetSigma=1>, <kNeighborhood=50>',\
    'Default': ''},\
  'JHCT': {\
    'Details': 'Jensen-Havrda-Charvet-Tsallis',\
    'Format': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>, <pointSetSigma=1>, <kNeighborhood=50>, <alpha=1.1>, <useAnisotropicCovariances=1>',\
    'Default': ''}\
}