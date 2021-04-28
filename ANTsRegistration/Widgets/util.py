import qt

#
# Delegates
#

class ComboDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    combo = qt.QComboBox(parent)
    li = []
    li.append("Zero")
    li.append("One")
    li.append("Two")
    li.append("Three")
    li.append("Four")
    li.append("Five")
    combo.addItems(li)
    self.connect(combo, qt.SIGNAL("currentIndexChanged(int)"), self, qt.SLOT("currentIndexChanged()"))
    return combo

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.setCurrentText(index.model().data(index))
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.currentText)

  @qt.Slot()
  def currentIndexChanged(self):
    print('a')
    # self.commitData.emit(self.sender())

class SpinBoxDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    spinBox = qt.QDoubleSpinBox(parent)
    spinBox.setSingleStep(0.1)
    # self.connect(combo, qt.SIGNAL("currentIndexChanged(int)"), self, qt.SLOT("currentIndexChanged()"))
    return spinBox

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.value = index.model().data(index) if index.model().data(index) else 0
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.value)

  @qt.Slot()
  def currentIndexChanged(self):
    print('a')

class TextEditDelegate(qt.QItemDelegate):
  def __init__(self, parent):
    qt.QItemDelegate.__init__(self, parent)

  def createEditor(self, parent, option, index):
    textEdit = qt.QPlainTextEdit(parent)
    textEdit.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    textEdit.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
    textEdit.setLineWrapMode(textEdit.NoWrap)
    # self.connect(combo, qt.SIGNAL("currentIndexChanged(int)"), self, qt.SLOT("currentIndexChanged()"))
    return textEdit

  def setEditorData(self, editor, index):
    editor.blockSignals(True)
    editor.plainText = index.model().data(index) if index.model().data(index) else ''
    editor.blockSignals(False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.plainText)

  @qt.Slot()
  def currentIndexChanged(self):
    print('a')

#
# Tables
#

class CustomTable(qt.QWidget):
  def __init__(self, columnNames):
    super().__init__()

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
    self.view.setModel(self.model)

    layout = qt.QGridLayout(self)
    layout.addWidget(self.addButton,0,0,1,1)
    layout.addWidget(self.removeButton,0,1,1,1)
    layout.addWidget(self.view,1,0,1,2)
  
  def onAddButton(self):
    self.model.insertRow(self.model.rowCount(qt.QModelIndex()))
  
  def onRemoveButton(self):
    selectedRows = self.view.selectionModel().selectedRows()
    for selectedRow in selectedRows:
      self.model.removeRow(selectedRow.row())



class StagesTable(CustomTable):
  def __init__(self):
    columnNames = ['Transform', 'Grid Step', 'Settings']
    CustomTable.__init__(self, columnNames)

    self.view.setItemDelegateForColumn(0, ComboDelegate(self.model))
    self.view.setItemDelegateForColumn(1, SpinBoxDelegate(self.model))
    self.view.setItemDelegateForColumn(2, TextEditDelegate(self.model))


class MetricsTable(CustomTable):

  Metrics = {\
    'CC': 'radius,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]',\
    'MI': 'numberOfBins,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]',\
    'Mattes': 'numberOfBins,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]',\
    'MeanSquares': 'radius=NA,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]',\
    'Demons': 'radius=NA,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]',\
    'GC': 'radius=NA,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]',\
  }

  def __init__(self):
    columnNames = ['Type', 'Fixed', 'Moving', 'Weight', 'Settings']
    CustomTable.__init__(self, columnNames)

    self.view.setItemDelegateForColumn(0, ComboDelegate(self.model))