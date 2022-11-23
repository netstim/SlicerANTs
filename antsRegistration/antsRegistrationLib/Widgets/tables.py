from posixpath import basename
import qt, ctk, slicer
from .delegates import ComboDelegate, MRMLComboDelegate, SpinBoxDelegate, TextEditDelegate
from ..util import antsBase, antsTransform, antsMetric
import os, glob

class CustomTable(qt.QWidget):

  RowHeight = 25

  def __init__(self, columnNames):
    qt.QWidget.__init__(self)

    self.addButton = qt.QPushButton('+')
    self.addButton.clicked.connect(self.onAddButton)

    self.removeButton = qt.QPushButton('-')
    self.removeButton.clicked.connect(self.onRemoveButton)

    self.linkStagesPushButton = qt.QPushButton('Link Across Stages')
    self.linkStagesPushButton.toolTip = 'When checked, settings will be the same for all stages.'
    self.linkStagesPushButton.checkable = True

    self.buttonsFrame = qt.QFrame()
    self.buttonsFrame.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Minimum)
    self.buttonsFrame.setLayout(qt.QHBoxLayout())
    self.buttonsFrame.layout().addWidget(self.addButton)
    self.buttonsFrame.layout().addWidget(self.removeButton)
    self.buttonsFrame.layout().addWidget(self.linkStagesPushButton)

    self.model = qt.QStandardItemModel(1, len(columnNames))
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
    self.view.setFixedHeight(65)
    self.view.setModel(self.model)
    self.view.setCurrentIndex(self.model.index(0,0))

    self.view.selectionModel().selectionChanged.connect(self.onSelectionChanged)

    self._layout = qt.QVBoxLayout(self)
    self._layout.addWidget(self.buttonsFrame)
    self._layout.addWidget(self.view)

  def onAddButton(self):
    self.addRowAndSetHeight()
    newRowN = self.model.rowCount()-1
    self.setDefaultNthRow(newRowN)
    self.view.setCurrentIndex(self.model.index(newRowN,0))

  def addRowAndSetHeight(self):
    self.model.insertRow(self.model.rowCount())
    self.view.setFixedHeight(self.view.height+self.RowHeight)

  def onRemoveButton(self):
    if self.model.rowCount() == 1:
      return
    else:
      self.removeSelectedRow()
  
  def removeSelectedRow(self):
    selectedRow = self.getSelectedRow()
    if selectedRow is not None:
      self.removeRowAndSetHeight(selectedRow)

  def removeRowAndSetHeight(self, rowNumber):
    self.model.removeRow(rowNumber)
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
      parameters[self.camelCaseHeader(col)] = data
    return parameters

  def camelCaseHeader(self, column):
    out = self.model.headerData(column, qt.Qt.Horizontal)
    out = out.replace(' ', '')
    return out[0].lower() + out[1:]

  def setGUIFromParameters(self, parameters):
    for N,params in enumerate(parameters):
      if N == self.model.rowCount():
        self.addRowAndSetHeight()
      self.setNthRowGUIFromParameters(N, params)
    while self.model.rowCount()-1 > N:
      self.removeRowAndSetHeight(self.model.rowCount()-1)

  def setNthRowGUIFromParameters(self, N, parameters):
    for col,val in enumerate(parameters.values()):
      index = self.model.index(N, col)
      try: # check if value is mrml node and save as user role
        node = slicer.util.getNode(val)
        self.model.setData(index, val, qt.Qt.UserRole)
        val = node.GetName()
      except:
        pass
      self.model.setData(index, val, qt.Qt.DisplayRole)


class TableWithSettings(CustomTable):
  def __init__(self, columnNames, comboItems):
    CustomTable.__init__(self, columnNames)

    self.settingsFormatText = ctk.ctkFittedTextBrowser()
    self.settingsFormatText.setFrameShape(qt.QFrame.NoFrame)
    self.settingsFormatText.setFrameShadow(qt.QFrame.Plain)
    self.settingsFormatText.setCollapsibleText('')

    gb = ctk.ctkCollapsibleGroupBox()
    gb.title = 'Settings Format'
    gb.collapsed = True
    gblayout = qt.QVBoxLayout(gb)
    gblayout.addWidget(self.settingsFormatText)

    self._layout.addWidget(gb)

    self.view.setItemDelegateForColumn(0, ComboDelegate(self.model, comboItems, self.setSettingsFormatTextFromName))
    self.view.setItemDelegateForColumn(self.model.columnCount()-1, TextEditDelegate(self.model))

  def onSelectionChanged(self, selection):
    CustomTable.onSelectionChanged(self, selection)
    indexes = selection.indexes()
    if indexes:
      name = self.model.data(indexes[0].siblingAtColumn(0))
      self.setSettingsFormatTextFromName(name)
      
  def setSettingsFormatTextFromName(self, name):
    text = antsBase().getSubClassByName(name).settingsFormat
    self.settingsFormatText.setCollapsibleText(text)


class StagesTable(TableWithSettings):
  def __init__(self):
    columnNames = ['Transform', 'Settings']
    comboItems = antsTransform().getSubClassesNames()
    TableWithSettings.__init__(self, columnNames, comboItems)

    self.settingsFormatText.setToolTip("The gradientStep or learningRate characterizes the gradient descent optimization and is scaled appropriately for each transform using the shift scales estimator. Subsequent parameters are transform-specific and can be determined from the usage. For the B-spline transforms one can also specify the smoothing in terms of spline distance (i.e. knot spacing).")
    self.linkStagesPushButton.delete()

    self.savePresetPushButton = qt.QPushButton('Save as preset')
    self.buttonsFrame.layout().addWidget(self.savePresetPushButton)

  def setDefaultNthRow(self, N):
    index = self.model.index(N, 0)
    aboveData =  self.model.data(index.siblingAtRow(N-1))
    if aboveData == 'Rigid':
      newData = 'Affine'
    else:
      newData = 'SyN'
    self.model.setData(index, newData)

  def onRemoveButton(self):
    pass # this is handled by antsRegistration Widget


class MetricsTable(TableWithSettings):
  def __init__(self):
    columnNames = ['Type', 'Fixed', 'Moving', 'Settings']
    comboItems = antsMetric().getSubClassesNames()
    TableWithSettings.__init__(self, columnNames, comboItems)

    self.settingsFormatText.setToolTip(" The 'metricWeight' variable is used to modulate the per stage weighting of the metrics. The metrics can also employ a sampling strategy defined by a sampling percentage. The sampling strategy defaults to 'None' (aka a dense sampling of one sample per voxel), otherwise it defines a point set over which to optimize the metric. The point set can be on a regular lattice or a random lattice of points slightly perturbed to minimize aliasing artifacts. samplingPercentage defines the fraction of points to select from the domain.")
    self.linkStagesPushButton.toolTip = self.linkStagesPushButton.toolTip + ' For Metrics enabled is the default. When disabled, only the first stage metric modifies the global selectors on the top of the GUI.'
    self.linkStagesPushButton.checked = True
    
    self.view.setItemDelegateForColumn(1, MRMLComboDelegate(self.model))
    self.view.setItemDelegateForColumn(2, MRMLComboDelegate(self.model))

  def setDefaultNthRow(self, N):
    index = self.model.index(N, 0)
    self.model.setData(index, 'MI')


class LevelsTable(CustomTable):
  def __init__(self):
    columnNames = ['Convergence', 'Smoothing Sigmas', 'Shrink Factors']
    CustomTable.__init__(self, columnNames)

    self.view.setItemDelegateForColumn(0, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(1, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(2, SpinBoxDelegate(self.model))

    self.smoothingSigmasUnitComboBox = qt.QComboBox()
    self.smoothingSigmasUnitComboBox.addItems(['vox', 'mm'])

    self.convergenceThresholdSpinBox = qt.QSpinBox()

    self.convergenceWindowSizeSpinBox = qt.QSpinBox()

    levelsSettingsFrame = qt.QFrame()
    levelsSettingsFrame.setLayout(qt.QFormLayout())
    levelsSettingsFrame.layout().addRow('Smoothing Sigmas Unit: ', self.smoothingSigmasUnitComboBox)
    levelsSettingsFrame.layout().addRow('Convergence Threshold (1e-N): ', self.convergenceThresholdSpinBox)
    levelsSettingsFrame.layout().addRow('Convergence Window Size: ', self.convergenceWindowSizeSpinBox)

    self._layout.addWidget(levelsSettingsFrame)

  def setDefaultNthRow(self, N):
    for column in range(3):
      index = self.model.index(N, column)
      aboveIndex =  index.siblingAtRow(N-1)
      newData = max(1, round(self.model.data(aboveIndex) * 0.5))
      self.model.setData(index, newData)

  def getParametersFromGUI(self):
    parameters = {}
    parameters['steps'] = super().getParametersFromGUI()
    parameters['smoothingSigmasUnit'] = self.smoothingSigmasUnitComboBox.currentText
    parameters['convergenceThreshold'] = self.convergenceThresholdSpinBox.value
    parameters['convergenceWindowSize'] = self.convergenceWindowSizeSpinBox.value
    return parameters

  def setGUIFromParameters(self, parameters):
    super().setGUIFromParameters(parameters['steps'])
    self.smoothingSigmasUnitComboBox.currentText = parameters['smoothingSigmasUnit']
    self.convergenceThresholdSpinBox.value = int(parameters['convergenceThreshold'])
    self.convergenceWindowSizeSpinBox.value = int(parameters['convergenceWindowSize'])
