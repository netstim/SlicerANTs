import os, sys
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import json
import shutil
import glob
import re

from antsRegistrationLib.Widgets.tables import StagesTable, MetricsTable, LevelsTable

#
# antsRegistration
#

class antsRegistration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "General Registration (ANTs)"
    self.parent.categories = ["Registration"]
    self.parent.dependencies = []
    self.parent.contributors = ["Simon Oxenford (Netstim Berlin)"]
    self.parent.helpText = """
See more information in <a href="https://github.com/simonoxen/SlicerANTs">module documentation</a>.
"""
    self.parent.acknowledgementText = ""



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

    self.ui.stagesTableWidget = StagesTable()
    stagesTableLayout = qt.QVBoxLayout(self.ui.stagesFrame)
    stagesTableLayout.addWidget(self.ui.stagesTableWidget)

    self.ui.metricsTableWidget = MetricsTable()
    metricsTableLayout = qt.QVBoxLayout(self.ui.metricsFrame)
    metricsTableLayout.addWidget(self.ui.metricsTableWidget)

    self.ui.levelsTableWidget = LevelsTable()
    levelsTableLayout = qt.QVBoxLayout(self.ui.levelsFrame)
    levelsTableLayout.addWidget(self.ui.levelsTableWidget)

    self.ui.cliWidget = slicer.modules.antscommand.createNewWidgetRepresentation()
    self.layout.addWidget(self.ui.cliWidget.children()[3]) # progress bar

    self.ui.outputLogText = ctk.ctkFittedTextBrowser()
    infoBox = ctk.ctkCollapsibleGroupBox()
    infoBox.title = 'Information'
    infoBoxLayout = qt.QVBoxLayout(infoBox)
    infoBoxLayout.addWidget(self.ui.outputLogText)
    self.layout.addWidget(infoBox)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = antsRegistrationLogic()

    self.ui.stagesPresetsComboBox.addItems(['Select...'] + PresetManager().getPresetNames())

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)


    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.stagesTableWidget.view.selectionModel().selectionChanged.connect(self.updateParameterNodeFromGUI)
    self.ui.outputInterpolationComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.outputTransformComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputVolumeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputLogTextComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformTypeComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.dimensionalitySpinBox.connect("valueChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.histogramMatchingCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.winsorizeRangeWidget.connect("rangeChanged(double,double)", self.updateParameterNodeFromGUI)
    self.ui.computationPrecisionComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)

    self.ui.fixedImageNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateStagesFromFixedMovingNodes)
    self.ui.movingImageNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateStagesFromFixedMovingNodes)

    # Stages Parameter
    self.ui.stagesTableWidget.removeButton.clicked.connect(self.onRemoveStageButtonClicked)
    self.ui.metricsTableWidget.removeButton.clicked.connect(self.updateStagesParameterFromGUI)
    self.ui.levelsTableWidget.removeButton.clicked.connect(self.updateStagesParameterFromGUI)
    self.ui.stagesTableWidget.model.itemChanged.connect(self.updateStagesParameterFromGUI)
    self.ui.metricsTableWidget.model.itemChanged.connect(self.updateStagesParameterFromGUI)
    self.ui.levelsTableWidget.model.itemChanged.connect(self.updateStagesParameterFromGUI)
    self.ui.fixedMaskComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateStagesParameterFromGUI)
    self.ui.movingMaskComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateStagesParameterFromGUI)
    self.ui.levelsTableWidget.smoothingSigmasUnitComboBox.currentTextChanged.connect(self.updateStagesParameterFromGUI)
    self.ui.levelsTableWidget.convergenceThresholdSpinBox.valueChanged.connect(self.updateStagesParameterFromGUI)
    self.ui.levelsTableWidget.convergenceWindowSizeSpinBox.valueChanged.connect(self.updateStagesParameterFromGUI)
    self.ui.metricsTableWidget.linkStagesPushButton.toggled.connect(self.updateStagesParameterFromGUI)
    self.ui.levelsTableWidget.linkStagesPushButton.toggled.connect(self.updateStagesParameterFromGUI)
    self.ui.linkMaskingStagesPushButton.toggled.connect(self.updateStagesParameterFromGUI)

    # Preset Stages
    self.ui.stagesPresetsComboBox.currentTextChanged.connect(self.onPresetSelected)

    # Buttons
    self.ui.stagesTableWidget.savePresetPushButton.connect('clicked(bool)', self.onSavePresetPushButton)
    self.ui.runRegistrationButton.connect('clicked(bool)', self.onRunRegistrationButton)

    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

    # Init tables
    self.ui.stagesTableWidget.view.selectionModel().emitSelectionChanged(self.ui.stagesTableWidget.view.selectionModel().selection, qt.QItemSelection())
    self.ui.metricsTableWidget.view.selectionModel().emitSelectionChanged(self.ui.metricsTableWidget.view.selectionModel().selection, qt.QItemSelection())

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

    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    self.ui.stagesTableWidget.view.setCurrentIndex(self.ui.stagesTableWidget.model.index(currentStage, 0))
    self.ui.stagePropertiesCollapsibleButton.text = 'Stage ' + str(currentStage + 1) + ' Properties'
    self.updateStagesGUIFromParameter()

    self.ui.outputTransformComboBox.setCurrentNode(self._parameterNode.GetNodeReference("OutputTransform"))
    self.ui.outputVolumeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
    self.ui.outputLogTextComboBox.setCurrentNode(self._parameterNode.GetNodeReference("OutputLog"))
    self.ui.outputInterpolationComboBox.currentText = self._parameterNode.GetParameter("OutputInterpolation")

    self.ui.initialTransformTypeComboBox.currentIndex = int(self._parameterNode.GetParameter("initializationFeature")) + 2
    self.ui.initialTransformNodeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("InitialTransform") if self.ui.initialTransformTypeComboBox.currentIndex == 1 else None)
    self.ui.initialTransformNodeComboBox.enabled = self.ui.initialTransformTypeComboBox.currentIndex == 1

    self.ui.dimensionalitySpinBox.value = int(self._parameterNode.GetParameter("Dimensionality"))
    self.ui.histogramMatchingCheckBox.checked = int(self._parameterNode.GetParameter("HistogramMatching"))
    self.ui.winsorizeRangeWidget.setMinimumValue(float(self._parameterNode.GetParameter("WinsorizeImageIntensities").split(",")[0]))
    self.ui.winsorizeRangeWidget.setMaximumValue(float(self._parameterNode.GetParameter("WinsorizeImageIntensities").split(",")[1]))
    self.ui.computationPrecisionComboBox.currentText = self._parameterNode.GetParameter("ComputationPrecision")

    self.ui.runRegistrationButton.enabled = self.ui.fixedImageNodeComboBox.currentNodeID and self.ui.movingImageNodeComboBox.currentNodeID

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateStagesGUIFromParameter(self):
    stagesList = json.loads(self._parameterNode.GetParameter("StagesJson"))
    self.ui.fixedImageNodeComboBox.setCurrentNodeID(stagesList[0]['metrics'][0]['fixed'])
    self.ui.movingImageNodeComboBox.setCurrentNodeID(stagesList[0]['metrics'][0]['moving'])
    self.setTransformsGUIFromList(stagesList)
    self.setCurrentStagePropertiesGUIFromList(stagesList)

  def setTransformsGUIFromList(self, stagesList):
    transformsParameters = [stage['transformParameters'] for stage in stagesList]
    self.ui.stagesTableWidget.setGUIFromParameters(transformsParameters)

  def setCurrentStagePropertiesGUIFromList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    if {'metrics','levels','masks'} <= set(stagesList[currentStage].keys()):
      self.ui.metricsTableWidget.setGUIFromParameters(stagesList[currentStage]['metrics'])
      self.ui.levelsTableWidget.setGUIFromParameters(stagesList[currentStage]['levels'])
      self.ui.fixedMaskComboBox.setCurrentNodeID(stagesList[currentStage]['masks']['fixed'])
      self.ui.movingMaskComboBox.setCurrentNodeID(stagesList[currentStage]['masks']['moving'])


  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetParameter("CurrentStage", str(self.ui.stagesTableWidget.getSelectedRow()))
    
    self._parameterNode.SetNodeReferenceID("OutputTransform", self.ui.outputTransformComboBox.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputVolumeComboBox.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputLog", self.ui.outputLogTextComboBox.currentNodeID)
    self._parameterNode.SetParameter("OutputInterpolation", self.ui.outputInterpolationComboBox.currentText)

    self._parameterNode.SetParameter("initializationFeature", str(self.ui.initialTransformTypeComboBox.currentIndex-2))
    self._parameterNode.SetNodeReferenceID("InitialTransform", self.ui.initialTransformNodeComboBox.currentNodeID)

    self._parameterNode.SetParameter("Dimensionality", str(self.ui.dimensionalitySpinBox.value))
    self._parameterNode.SetParameter("HistogramMatching", str(int(self.ui.histogramMatchingCheckBox.checked)))
    self._parameterNode.SetParameter("WinsorizeImageIntensities", ",".join([str(self.ui.winsorizeRangeWidget.minimumValue),str(self.ui.winsorizeRangeWidget.maximumValue)]))
    self._parameterNode.SetParameter("ComputationPrecision",  self.ui.computationPrecisionComboBox.currentText)

    self._parameterNode.EndModify(wasModified)


  def updateStagesFromFixedMovingNodes(self):
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    stagesList = json.loads(self._parameterNode.GetParameter("StagesJson"))
    for stage in stagesList:
      stage['metrics'][0]['fixed'] = self.ui.fixedImageNodeComboBox.currentNodeID
      stage['metrics'][0]['moving'] = self.ui.movingImageNodeComboBox.currentNodeID
    self._parameterNode.SetParameter("StagesJson", json.dumps(stagesList))

  def updateStagesParameterFromGUI(self):
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    stagesList = json.loads(self._parameterNode.GetParameter("StagesJson"))
    self.setStagesTransformsToStagesList(stagesList)
    self.setCurrentStagePropertiesToStagesList(stagesList)
    self._parameterNode.SetParameter("StagesJson", json.dumps(stagesList))

  def setStagesTransformsToStagesList(self, stagesList):
    for stageNumber,transformParameters in enumerate(self.ui.stagesTableWidget.getParametersFromGUI()):
      if stageNumber == len(stagesList):
        stagesList.append({})
      stagesList[stageNumber]['transformParameters'] = transformParameters

  def setCurrentStagePropertiesToStagesList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))

    stagesIterator = range(len(stagesList)) if self.ui.metricsTableWidget.linkStagesPushButton.checked else [currentStage]
    for stageNumber in stagesIterator:
      stagesList[stageNumber]['metrics'] = self.ui.metricsTableWidget.getParametersFromGUI()

    stagesIterator = range(len(stagesList)) if self.ui.levelsTableWidget.linkStagesPushButton.checked else [currentStage]
    for stageNumber in stagesIterator:
      stagesList[stageNumber]['levels'] = self.ui.levelsTableWidget.getParametersFromGUI()

    stagesIterator = range(len(stagesList)) if self.ui.linkMaskingStagesPushButton.checked else [currentStage]
    for stageNumber in stagesIterator:
      stagesList[stageNumber]['masks'] = {'fixed': self.ui.fixedMaskComboBox.currentNodeID, 'moving': self.ui.movingMaskComboBox.currentNodeID}

  def onRemoveStageButtonClicked(self):
    stagesList = json.loads(self._parameterNode.GetParameter("StagesJson"))
    if len(stagesList) == 1:
      return
    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    stagesList.pop(currentStage)
    wasModified = self._parameterNode.StartModify()  # Modify in a single batch
    self._parameterNode.SetParameter("CurrentStage", str(max(currentStage-1,0)))
    self._parameterNode.SetParameter("StagesJson", json.dumps(stagesList))
    self._parameterNode.EndModify(wasModified)

  def onPresetSelected(self, presetName):
    if presetName == 'Select...' or self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    wasModified = self._parameterNode.StartModify()  # Modify in a single batch
    presetParameters = PresetManager().getPresetParametersByName(presetName)
    for stage in presetParameters['stages']:
      stage['metrics'][0]['fixed'] = self.ui.fixedImageNodeComboBox.currentNodeID
      stage['metrics'][0]['moving'] = self.ui.movingImageNodeComboBox.currentNodeID
    self._parameterNode.SetParameter("StagesJson", json.dumps(presetParameters['stages']))
    self._parameterNode.SetParameter("CurrentStage", "0")
    self._parameterNode.EndModify(wasModified)

  def onSavePresetPushButton(self):
    stages = json.loads(self._parameterNode.GetParameter("StagesJson"))
    for stage in stages:
      for metric in stage['metrics']:
        metric['fixed'] = None
        metric['moving'] = None
      stage['masks']['fixed'] = None
      stage['masks']['moving'] = None
    savedPresetName = PresetManager().saveStagesAsPreset(stages)
    if savedPresetName:
      self._updatingGUIFromParameterNode = True
      self.ui.stagesPresetsComboBox.addItem(savedPresetName)
      self.ui.stagesPresetsComboBox.setCurrentText(savedPresetName)
      self._updatingGUIFromParameterNode = False


  def onRunRegistrationButton(self):
    if self.ui.runRegistrationButton.text == 'Cancel':
      self.logic.cancelRegistration()
      return

    parameters = {}
    parameters['stages'] = json.loads(self._parameterNode.GetParameter("StagesJson"))
    # ID to Node
    for stage in parameters['stages']:
      for metric in stage['metrics']:
        metric['fixed'] = slicer.util.getNode(metric['fixed'])
        metric['moving'] = slicer.util.getNode(metric['moving'])
      stage['masks']['fixed'] = slicer.util.getNode(stage['masks']['fixed']) if stage['masks']['fixed'] else ''
      stage['masks']['moving'] = slicer.util.getNode(stage['masks']['moving']) if stage['masks']['moving'] else ''

    parameters['outputSettings'] = {}
    parameters['outputSettings']['transform'] = self.ui.outputTransformComboBox.currentNode()
    parameters['outputSettings']['volume'] = self.ui.outputVolumeComboBox.currentNode()
    parameters['outputSettings']['interpolation'] = self.ui.outputInterpolationComboBox.currentText
    parameters['outputSettings']['log'] = self.ui.outputLogTextComboBox.currentNode()

    parameters['initialTransformSettings'] = {}
    parameters['initialTransformSettings']['initializationFeature'] = int(self._parameterNode.GetParameter("initializationFeature"))
    parameters['initialTransformSettings']['initialTransformNode'] = self.ui.initialTransformNodeComboBox.currentNode()

    parameters['generalSettings'] = {}
    parameters['generalSettings']['dimensionality'] = self.ui.dimensionalitySpinBox.value
    parameters['generalSettings']['histogramMatching'] = int(self.ui.histogramMatchingCheckBox.checked)
    parameters['generalSettings']['winsorizeImageIntensities'] = [self.ui.winsorizeRangeWidget.minimumValue, self.ui.winsorizeRangeWidget.maximumValue]
    parameters['generalSettings']['computationPrecision'] = self.ui.computationPrecisionComboBox.currentText

    self.ui.outputLogText.setText("")

    self.logic.process(**parameters)

    updateLogTimer = qt.QTimer()
    updateLogTimer.timeout.connect(self.updateLog)
    updateLogTimer.start(500)

    self.ui.cliWidget.setCurrentCommandLineModuleNode(self.logic._cliNode)
    self.logic._cliNode.AddObserver('ModifiedEvent', self.onProcessingStatusUpdate)
    self.logic._cliNode.AddObserver('ModifiedEvent', lambda c,e,t=updateLogTimer: self.deleteTimerIfFinished(c,e,t))
    self.ui.runRegistrationButton.text = 'Cancel'


  def onProcessingStatusUpdate(self, caller, event):
    if (caller.GetStatus() & caller.Cancelled):
      self.ui.runRegistrationButton.text = "Run Registration"
      self.ui.outputLogText.setText("Canceled")
    elif (caller.GetStatus() & caller.Completed):
      self.ui.runRegistrationButton.text = "Run Registration"
      if (caller.GetStatus() & caller.ErrorsMask):
        self.ui.outputLogText.setText("Error: see output window")
      else:
        self.ui.outputLogText.setText("Finished Registration")
    else:
      self.ui.runRegistrationButton.text = "Cancel"

  def updateLog(self):
    outText = self.logic.getCurrentRunningStage()
    lastLine = self.logic.getLastNLogLines(1)
    if re.search("\d+DIAGNOSTIC.*", lastLine):
      info = ['XXDIAGNOSTIC', 'Iteration', 'metricValue', 'convergenceValue', 'ITERATION_TIME_INDEX', 'SINCE_LAST']
      infoMap = list(map(lambda x,y: "%s: %s"% (x,y), info, lastLine[:-1].split(',')))
      lastLine = '\n'.join(infoMap[1:4])
    outText = outText + '\n' + lastLine
    self.ui.outputLogText.setText(outText)

  def deleteTimerIfFinished(self, caller, event, updateLogTimer):
    if (caller.GetStatus() & caller.Cancelled) or (caller.GetStatus() & caller.Completed):
      if updateLogTimer:
        updateLogTimer.stop()
        updateLogTimer.delete()


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
    if slicer.util.settingsValue('Developer/DeveloperMode', False, converter=slicer.util.toBool):
      import importlib
      import antsRegistrationLib
      antsRegistrationLibPath = os.path.join(os.path.dirname(__file__), 'antsRegistrationLib')
      G = glob.glob(os.path.join(antsRegistrationLibPath, '**','*.py'))
      for g in G:
        relativePath = os.path.relpath(g, antsRegistrationLibPath) # relative path
        relativePath = os.path.splitext(relativePath)[0] # get rid of .py
        moduleParts = relativePath.split(os.path.sep) # separate
        importlib.import_module('.'.join(['antsRegistrationLib']+moduleParts)) # import module
        module = antsRegistrationLib
        for modulePart in moduleParts: # iterate over parts in order to load subpkgs
          module = getattr(module, modulePart)
        importlib.reload(module) # reload

    self.antsApplyTransformsCommand = ''
    self.tempDirectory = ''
    self.outputVolumeFileName = 'outputVolume.nii'
    self.outputTransformPrefix = 'outputTransform'
    self.outputLog = 'out.txt'
    self._cliNode = None
    self._cliObserver = None
    self._outputVolume = None
    self._outputTransform = None
    self._outputLog = None
    
  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    presetParameters = PresetManager().getPresetParametersByName()
    if not parameterNode.GetParameter("StagesJson"):
      parameterNode.SetParameter("StagesJson",  json.dumps(presetParameters["stages"]))
    if not parameterNode.GetParameter("CurrentStage"):
      parameterNode.SetParameter("CurrentStage", "0")

    if not parameterNode.GetParameter("OutputTransform"):
      parameterNode.SetParameter("OutputTransform", "")
    if not parameterNode.GetParameter("OutputVolume"):
      parameterNode.SetParameter("OutputVolume", "")
    if not parameterNode.GetParameter("OutputLog"):
      parameterNode.SetParameter("OutputLog", "")
    if not parameterNode.GetParameter("OutputInterpolation"):
      parameterNode.SetParameter("OutputInterpolation", str(presetParameters["outputSettings"]["interpolation"]))

    if not parameterNode.GetParameter("initializationFeature"):
      parameterNode.SetParameter("initializationFeature", str(presetParameters["initialTransformSettings"]["initializationFeature"]))
    if not parameterNode.GetParameter("InitialTransform"):
      parameterNode.SetParameter("InitialTransform", "")

    if not parameterNode.GetParameter("Dimensionality"):
      parameterNode.SetParameter("Dimensionality", str(presetParameters["generalSettings"]["dimensionality"]))
    if not parameterNode.GetParameter("HistogramMatching"):
      parameterNode.SetParameter("HistogramMatching", str(presetParameters["generalSettings"]["histogramMatching"]))
    if not parameterNode.GetParameter("WinsorizeImageIntensities"):
      parameterNode.SetParameter("WinsorizeImageIntensities", ",".join([str(x) for x in presetParameters["generalSettings"]["winsorizeImageIntensities"]]))
    if not parameterNode.GetParameter("ComputationPrecision"):
      parameterNode.SetParameter("ComputationPrecision", presetParameters["generalSettings"]["computationPrecision"])

  def cancelRegistration(self):
    if self._cliNode:
      self._cliNode.Cancel()

  def process(self, stages, outputSettings, initialTransformSettings={}, generalSettings={}):
    """
    :param stages: list defining registration stages
    :param outputSettings: dictionary defining output settings
    :param initialTransformSettings: dictionary defining initial moving transform
    :param generalSettings: dictionary defining general registration settings
    See presets examples to see how these are specified
    """
    self.resetTempDirectoryAndLocalVars()

    initialTransformSettings['fixedImageNode'] = stages[0]['metrics'][0]['fixed']
    initialTransformSettings['movingImageNode'] = stages[0]['metrics'][0]['moving']

    antsRegistraionCommand = self.getAntsRegistrationCommand(stages, outputSettings, initialTransformSettings, generalSettings)
    self.runAntsCommandAndSetObserver('antsRegistration', antsRegistraionCommand)

    if isinstance(outputSettings['transform'], slicer.vtkMRMLGridTransformNode):
      gridReferenceNode = stages[0]['metrics'][0]['fixed']
      self.antsApplyTransformsCommand = self.getAntsApplyTransformsCommand(gridReferenceNode)
    else:
      self.antsApplyTransformsCommand = ''

    self._outputVolume = outputSettings['volume']
    self._outputTransform = outputSettings['transform']
    self._outputLog = outputSettings['log']

  def runAntsCommandAndSetObserver(self, executableName, command):
    self._cliNode = self.runAntsCommand(executableName, command)
    self._cliObserver = self._cliNode.AddObserver('ModifiedEvent', self.onProcessingStatusUpdate)

  def runAntsCommand(self, executableName, command):
    logging.info("Running ANTs Command: " + executableName + " " + command)
    params = {}
    params['antsExecutable'] = executableName
    params['antsCommand'] = command
    params['antsOutputLog'] = os.path.join(self.tempDirectory, self.outputLog)
    return slicer.cli.run(slicer.modules.antscommand, self._cliNode, params, wait_for_completion=False, update_display=False)

  def onProcessingStatusUpdate(self, caller, event):
    if (caller.GetStatus() & caller.Cancelled):
        self.onProcessFinished()
    elif (caller.GetStatus() & caller.Completed):
      if (caller.GetStatus() & caller.ErrorsMask):
        self.onProcessFinished()
      else:
        self._cliNode.RemoveObserver(self._cliObserver)
        self.doPostProcessing()
        
  def doPostProcessing(self):
    if self.antsApplyTransformsCommand is not '':
      self.runAntsCommandAndSetObserver('antsApplyTransforms', self.antsApplyTransformsCommand)
      self.antsApplyTransformsCommand = ''
      return

    if self._outputTransform is not None:
      self.loadOutputTransformNode(self._outputTransform)
    if self._outputVolume is not None:
      self.loadOutputVolumeNode(self._outputVolume)

    self.onProcessFinished()

  def onProcessFinished(self):
    if self._outputLog is not None:
      self.loadOutputLog(self._outputLog)
    self.printLastNLogLines()
    self.resetTempDirectoryAndLocalVars()

  def loadOutputTransformNode(self, outputTransformNode):
    fileExt = '.nii.gz' if isinstance(outputTransformNode, slicer.vtkMRMLGridTransformNode) else '.h5'
    outputTransformPath = os.path.join(self.getTempDirectory(), self.outputTransformPrefix + 'Composite' + fileExt)
    loadedOutputTransformNode = slicer.util.loadTransform(outputTransformPath)
    if not loadedOutputTransformNode.GetTransformToParent().GetInverseFlag():
      outputTransformNode.SetAndObserveTransformToParent(loadedOutputTransformNode.GetTransformToParent())
    else:
      outputTransformNode.SetAndObserveTransformFromParent(loadedOutputTransformNode.GetTransformFromParent())
    slicer.mrmlScene.RemoveNode(loadedOutputTransformNode)

  def loadOutputVolumeNode(self, outputVolumeNode):
    outputVolumePath = os.path.join(self.getTempDirectory(), self.outputVolumeFileName)
    loadedOutputVolumeNode = slicer.util.loadVolume(outputVolumePath)
    outputVolumeNode.SetAndObserveImageData(loadedOutputVolumeNode.GetImageData())
    ijkToRas = vtk.vtkMatrix4x4()
    loadedOutputVolumeNode.GetIJKToRASMatrix(ijkToRas)
    outputVolumeNode.SetIJKToRASMatrix(ijkToRas)
    slicer.mrmlScene.RemoveNode(loadedOutputVolumeNode)

  def loadOutputLog(self, outputLogNode):
    outputLogNode.SetText(self.getLastNLogLines(float('Inf')))

  def printLastNLogLines(self, N=20):
    print(self.getLastNLogLines(N))

  def getCurrentRunningStage(self):
    text = self.getLastNLogLines(float('Inf'))
    stageNumberMatch = [0] + [int(s)+1 for s in re.findall("(?<=Stage )\d+(?=\n)", text)]
    stageDescriptionMatch = [''] + re.findall("(?<=[*]{3} ).*(?= [*]{3})", text)
    levelsMatch = re.findall("DIAGNOSTIC,Iteration,metricValue,convergenceValue,ITERATION_TIME_INDEX,SINCE_LAST", text[text.index(stageDescriptionMatch[-1]):])
    return "Stage: %i\nLevel: %i\n%s" % (stageNumberMatch[-1], len(levelsMatch), stageDescriptionMatch[-1])
    
  def getLastNLogLines(self, N=20):
    logFile = os.path.join(self.tempDirectory, self.outputLog)
    with open(logFile) as f:
      lines = f.readlines()
      linesNumber = len(lines)
      if linesNumber:
        return ''.join(lines[-min(N,linesNumber-1):])
    return ''

  def resetTempDirectoryAndLocalVars(self):
    self.resetTempDirectory()
    self.resetCliNode()
    self._outputVolume = None
    self._outputTransform = None

  def resetCliNode(self):
    slicer.mrmlScene.RemoveNode(self._cliNode)
    self._cliNode = None
    self._cliObserver = None

  def getAntsApplyTransformsCommand(self, gridReferenceNode):
    antsCommand = "--transform %s" % os.path.join(self.getTempDirectory(), self.outputTransformPrefix + 'Composite.h5')
    antsCommand = antsCommand + " --reference-image %s" % self.saveNodeAndGetPath(gridReferenceNode)
    antsCommand = antsCommand + " --output [%s,1]" % os.path.join(self.getTempDirectory(), self.outputTransformPrefix + 'Composite.nii.gz')
    antsCommand = antsCommand + " --verbose 1"
    return antsCommand

  def getAntsRegistrationCommand(self, stages, outputSettings, initialTransformSettings={}, generalSettings={}):
    antsCommand = self.getGeneralSettingsCommand(**generalSettings)
    antsCommand = antsCommand + self.getOutputCommand(interpolation=outputSettings['interpolation'])
    antsCommand = antsCommand + self.getInitialMovingTransformCommand(**initialTransformSettings)
    for stage in stages:
      antsCommand = antsCommand + self.getStageCommand(**stage)
    return antsCommand

  def getGeneralSettingsCommand(self, dimensionality=3, histogramMatching=False, winsorizeImageIntensities=[0,1], computationPrecision="float"):
    command = "--dimensionality %i" % dimensionality
    command = command + " --use-histogram-matching %i" % histogramMatching
    command = command + " --winsorize-image-intensities [%.3f,%.3f]" % tuple(winsorizeImageIntensities)
    command = command + " --float %i" % (computationPrecision == "float")
    command = command + " --verbose 1"
    return command

  def getOutputCommand(self, interpolation='Linear'):
    command = " --interpolation %s" % interpolation
    command = command + " --output [%s,%s]" % (os.path.join(self.getTempDirectory(), self.outputTransformPrefix), os.path.join(self.getTempDirectory(), self.outputVolumeFileName))
    command = command + " --write-composite-transform 1"
    command = command + " --collapse-output-transforms 1"
    return command

  def getInitialMovingTransformCommand(self, initialTransformNode=None, initializationFeature=-1, fixedImageNode=None, movingImageNode=None):
    if initialTransformNode is not None:
      return " --initial-moving-transform %s" % self.saveNodeAndGetPath(initialTransformNode)
    elif initializationFeature >= 0:
      return " --initial-moving-transform [%s,%s,%i]" % (self.saveNodeAndGetPath(fixedImageNode), self.saveNodeAndGetPath(movingImageNode), initializationFeature)
    else:
      return ""

  def getStageCommand(self, transformParameters, metrics, levels, masks):
    command = self.getTransformCommand(**transformParameters)
    for metric in metrics:
      command = command + self.getMetricCommand(**metric)
    command = command + self.getLevelsCommand(**levels)
    command = command + self.getMasksCommand(**masks)
    return command

  def getTransformCommand(self, transform, settings):
    return " --transform %s[%s]" % (transform, settings)

  def getMetricCommand(self, type, fixed, moving, settings):
    return " --metric %s[%s,%s,%s]" % (type, self.saveNodeAndGetPath(fixed), self.saveNodeAndGetPath(moving), settings)

  def getMasksCommand(self, fixed=None, moving=None):
    fixedMask = self.saveNodeAndGetPath(fixed) if fixed else 'NULL'
    movingMask = self.saveNodeAndGetPath(moving) if moving else 'NULL'
    return " --masks [%s,%s]" % (fixedMask, movingMask)

  def getLevelsCommand(self, steps, convergenceThreshold, convergenceWindowSize, smoothingSigmasUnit):
    convergence = self.joinStepsInfoForKey(steps, 'convergence')
    smoothingSigmas = self.joinStepsInfoForKey(steps, 'smoothingSigmas')
    shrinkFactors = self.joinStepsInfoForKey(steps, 'shrinkFactors')
    command = " --convergence [%s,1e-%i,%i]" % (convergence, convergenceThreshold, convergenceWindowSize)
    command = command + " --smoothing-sigmas %s%s" % (smoothingSigmas, smoothingSigmasUnit)
    command = command + " --shrink-factors %s" % shrinkFactors
    command = command + " --use-estimate-learning-rate-once"
    return command

  def joinStepsInfoForKey(self, steps, key):
    out = [str(step[key]) for step in steps]
    return "x".join(out)

  def saveNodeAndGetPath(self, node):
    # New location definition
    if isinstance(node, slicer.vtkMRMLVolumeNode):
      fileExtension = '.nii'
    elif isinstance(node, slicer.vtkMRMLTransformNode):
      fileExtension =  '.h5'
    filePath = os.path.join(self.getTempDirectory(), node.GetID() + fileExtension)
    if os.path.isfile(filePath):
      return filePath # same node used in different metrics
    # Save original file paths
    originalFilePath = ""
    originalFilePaths = []
    storageNode = node.GetStorageNode()
    if storageNode:
      originalFilePath = storageNode.GetFileName()
      for fileIndex in range(storageNode.GetNumberOfFileNames()):
        originalFilePaths.append(storageNode.GetNthFileName(fileIndex))
    # Save to new location
    slicer.util.saveNode(node, filePath, {"useCompression": False})
    # Restore original file paths
    if storageNode:
      storageNode.ResetFileNameList()
      storageNode.SetFileName(originalFilePath)
      for fileIndex in range(storageNode.GetNumberOfFileNames()):
        storageNode.AddFileName(originalFilePaths[fileIndex])
    else:
      # temporary storage node was created, remove it to restore original state
      storageNode = node.GetStorageNode()
      slicer.mrmlScene.RemoveNode(storageNode)
    return filePath

  def resetTempDirectory(self):
    if os.path.isdir(self.tempDirectory):
      shutil.rmtree(self.tempDirectory)
    self.tempDirectory = ''

  def getTempDirectory(self):
    if not self.tempDirectory:
      tempDir = qt.QDir(self.getTempDirectoryBase())
      tempDirName = qt.QDateTime().currentDateTime().toString("yyyyMMdd_hhmmss_zzz")
      fileInfo = qt.QFileInfo(qt.QDir(tempDir), tempDirName)
      dirPath = fileInfo.absoluteFilePath()
      qt.QDir().mkpath(dirPath)
      self.tempDirectory = dirPath
    return self.tempDirectory

  def getTempDirectoryBase(self):
    tempDir = qt.QDir(slicer.app.temporaryPath)
    fileInfo = qt.QFileInfo(qt.QDir(tempDir), "antsRegistration")
    dirPath = fileInfo.absoluteFilePath()
    qt.QDir().mkpath(dirPath)
    return dirPath


#
# Preset Manager
#

class PresetManager():
  def __init__(self):
      self.presetPath = os.path.join(os.path.dirname(__file__),'Resources','Presets')

  def saveStagesAsPreset(self, stages):
    from PythonQt import BoolResult
    ok = BoolResult()
    presetName = qt.QInputDialog().getText(qt.QWidget(), 'Save Preset', 'Preset name: ', qt.QLineEdit.Normal, 'my_preset', ok)
    if not ok:
      return
    if presetName in self.getPresetNames():
      qt.QMessageBox().warning(qt.QWidget(),'Warning', presetName + ' already exists. Set another name.')
      self.saveStagesAsPreset(stages)
      return
    outFilePath = os.path.join(gself.presetPath, presetName + '.json')
    saveSettings = self.getPresetParametersByName()
    saveSettings['stages'] = self.removeNodesFromStages(stages)
    try:
      with open(outFilePath, 'w') as outfile:
        json.dump(saveSettings, outfile)
    except:
      qt.QMessageBox().warning(qt.QWidget(),'Warning', 'Unable to write into ' + outFilePath)
      return
    print('Saved preset to ' + outFilePath)
    return presetName

  def getPresetParametersByName(self, name='Rigid'):
    presetFilePath = os.path.join(self.presetPath, name + '.json')
    with open(presetFilePath) as presetFile:
      return json.load(presetFile)

  def getPresetNames(self):
    G = glob.glob(os.path.join(self.presetPath, '*.json'))
    return [os.path.splitext(os.path.basename(g))[0] for g in G]


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
    sampleDataLogic = SampleData.SampleDataLogic()
    tumor1 = sampleDataLogic.downloadMRBrainTumor1()
    tumor2 = sampleDataLogic.downloadMRBrainTumor2()

    outputVolume = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
    outputTransform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLGridTransformNode') # test antsApplyTransforms

    logic = antsRegistrationLogic()
    presetParameters = PresetManager().getPresetParametersByName('QuickSyN')
    for stage in presetParameters['stages']:
      for metric in stage['metrics']:
        metric['fixed'] = tumor1
        metric['moving'] = tumor2
      # let's make it quick
      for step in stage['levels']['steps']:
        step['shrinkFactors'] = 10
      stage['levels']['convergenceThreshold'] = 1
      stage['levels']['convergenceWindowSize'] = 5

    presetParameters['outputSettings']['volume'] = outputVolume
    presetParameters['outputSettings']['transform'] = outputTransform

    logic.process(**presetParameters)

    self.delayDisplay('Test passed!')

