import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import PythonQt
import platform

from Widgets.util import Abz


#
# antsRegistration
#

class antsRegistration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "antsRegistration"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Registration"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Simon Oxenford (Netstim Berlin)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#antsRegistration">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

#
# Custom Widgets
#

#
# Custom Qt
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
    # self.commi

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
    # self.commi


#
# antsRegistrationWidget
#

class antsRegistrationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/antsRegistration.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set custom UI components

    self.ui.stagesTableModel = qt.QStandardItemModel(0,3,uiWidget)
    self.ui.stagesTableModel.setHeaderData(0, qt.Qt.Horizontal, 'Transform')
    self.ui.stagesTableModel.setHeaderData(1, qt.Qt.Horizontal, 'Gradient Step')
    self.ui.stagesTableModel.setHeaderData(2, qt.Qt.Horizontal, 'Settings')
    self.ui.stagesTableView.setItemDelegateForColumn(0, ComboDelegate(self.ui.stagesTableModel))
    self.ui.stagesTableView.setItemDelegateForColumn(1, SpinBoxDelegate(self.ui.stagesTableModel))
    self.ui.stagesTableView.setItemDelegateForColumn(2, TextEditDelegate(self.ui.stagesTableModel))
    self.ui.stagesTableView.setModel(self.ui.stagesTableModel)    

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = antsRegistrationLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    # self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    # self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    # self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    # self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    # self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

    # Buttons
    self.ui.addStagePushButton.connect('clicked(bool)', self.onAddStagePushButton)
    self.ui.removeStagePushButton.connect('clicked(bool)', self.onRemoveStagePushButton)
    self.ui.runRegistrationButton.connect('clicked(bool)', self.onRunRegistrationButton)

    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    # self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    # self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
    # self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
    # self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
    # self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

    # # Update buttons states and tooltips
    # if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
    #   self.ui.applyButton.toolTip = "Compute output volume"
    #   self.ui.applyButton.enabled = True
    # else:
    #   self.ui.applyButton.toolTip = "Select input and output volume nodes"
    #   self.ui.applyButton.enabled = False

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    # self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
    # self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
    # self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
    # self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
    # self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

    self._parameterNode.EndModify(wasModified)


  def onAddStagePushButton(self):
    self.ui.stagesTableModel.insertRow(self.ui.stagesTableModel.rowCount(qt.QModelIndex()))

  def onRemoveStagePushButton(self):
    selection = self.ui.stagesTableView.selectionModel().selectedRows()
    for sel in selection:
      self.ui.stagesTableModel.removeRow(sel.row())

  def onRunRegistrationButton(self):
    """
    Run processing when user clicks "Apply" button.
    """
    pass
    # try:

    #   # Compute output
    #   self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
    #     self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

    #   # Compute inverted output (if needed)
    #   if self.ui.invertedOutputSelector.currentNode():
    #     # If additional output volume is selected then result with inverted threshold is written there
    #     self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
    #       self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

    # except Exception as e:
    #   slicer.util.errorDisplay("Failed to compute results: "+str(e))
    #   import traceback
    #   traceback.print_exc()


#
# antsRegistrationLogic
#

class antsRegistrationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")


  def getantsRegistrationExecutable(self):
    """
    Look for antsRegistration executable
    """
    executableExt = '.exe' if platform.system() == 'Windows' else ''
    executableFileName = 'antsRegistration' + executableExt
    scriptPath = os.path.dirname(os.path.abspath(__file__))
    antsBinDirCandidates = [
      os.path.join(scriptPath, '..'),
      os.path.join(scriptPath, '../../../bin'),
      os.path.join(scriptPath, '../../../../bin'),
      os.path.join(scriptPath, '../../../../bin/Release'),
      os.path.join(scriptPath, '../../../../bin/Debug'),
      os.path.join(scriptPath, '../../../../bin/RelWithDebInfo'),
      os.path.join(scriptPath, '../../../../bin/MinSizeRel') ]

    for antsBinDirCandidate in antsBinDirCandidates:
      antsExecutable = os.path.join(os.path.abspath(antsBinDirCandidate), executableFileName)
      if os.path.isfile(antsExecutable):
        return antsExecutable

    raise ValueError('ANTs not found')

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info('Processing completed in {0:.2f} seconds'.format(stopTime-startTime))

#
# antsRegistrationTest
#

class antsRegistrationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_antsRegistration1()

  def test_antsRegistration1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('antsRegistration1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = antsRegistrationLogic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')

