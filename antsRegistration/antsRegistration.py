import os, sys
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import platform
import json
import subprocess
import shutil
import glob

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
    self.parent.title = "General Registraion (ANTs)"
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

    G = glob.glob(os.path.join(os.path.dirname(__file__),'Resources','Presets','*.json'))
    presetNames = [os.path.splitext(os.path.basename(g))[0] for g in G]
    self.ui.stagesTableWidget.loadPresetComboBox.addItems(['Load from preset'] + presetNames)

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
    self.ui.stagesTableWidget.view.selectionModel().selectionChanged.connect(self.updateParameterNodeFromGUI)
    self.ui.outputInterpolationComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.outputTransformComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputVolumeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformTypeComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.dimensionalitySpinBox.connect("valueChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.histogramMatchingCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.winsorizeRangeWidget.connect("rangeChanged(double,double)", self.updateParameterNodeFromGUI)
    self.ui.computationPrecisionComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)

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
    self.ui.stagesTableWidget.loadPresetComboBox.currentTextChanged.connect(self.onPresetSelected)

    # Buttons
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
    self.ui.outputInterpolationComboBox.currentText = self._parameterNode.GetParameter("OutputInterpolation")
    self.ui.outputInterpolationComboBox.enabled = self._parameterNode.GetNodeReference("OutputVolume") is not None

    self.ui.initialTransformTypeComboBox.currentIndex = int(self._parameterNode.GetParameter("initializationFeature")) + 2
    self.ui.initialTransformNodeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("InitialTransform") if self.ui.initialTransformTypeComboBox.currentIndex == 1 else None)
    self.ui.initialTransformNodeComboBox.enabled = self.ui.initialTransformTypeComboBox.currentIndex == 1

    self.ui.dimensionalitySpinBox.value = int(self._parameterNode.GetParameter("Dimensionality"))
    self.ui.histogramMatchingCheckBox.checked = int(self._parameterNode.GetParameter("HistogramMatching"))
    self.ui.winsorizeRangeWidget.setMinimumValue(float(self._parameterNode.GetParameter("WinsorizeImageIntensities").split(",")[0]))
    self.ui.winsorizeRangeWidget.setMaximumValue(float(self._parameterNode.GetParameter("WinsorizeImageIntensities").split(",")[1]))
    self.ui.computationPrecisionComboBox.currentText = self._parameterNode.GetParameter("ComputationPrecision")

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateStagesGUIFromParameter(self):
    stagesList = json.loads(self._parameterNode.GetParameter("StagesJson"))
    self.setTransformsGUIFromList(stagesList)
    self.setCurrentStagePropertiesGUIFromList(stagesList)

  def setTransformsGUIFromList(self, stagesList):
    transformsParameters = [stage['transformParameters'] for stage in stagesList]
    self.ui.stagesTableWidget.setGUIFromParameters(transformsParameters)

  def setCurrentStagePropertiesGUIFromList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    if 'metrics' in stagesList[currentStage].keys():
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
    self._parameterNode.SetParameter("OutputInterpolation", self.ui.outputInterpolationComboBox.currentText)

    self._parameterNode.SetParameter("initializationFeature", str(self.ui.initialTransformTypeComboBox.currentIndex-2))
    self._parameterNode.SetNodeReferenceID("InitialTransform", self.ui.initialTransformNodeComboBox.currentNodeID)

    self._parameterNode.SetParameter("Dimensionality", str(self.ui.dimensionalitySpinBox.value))
    self._parameterNode.SetParameter("HistogramMatching", str(int(self.ui.histogramMatchingCheckBox.checked)))
    self._parameterNode.SetParameter("WinsorizeImageIntensities", ",".join([str(self.ui.winsorizeRangeWidget.minimumValue),str(self.ui.winsorizeRangeWidget.maximumValue)]))
    self._parameterNode.SetParameter("ComputationPrecision",  self.ui.computationPrecisionComboBox.currentText)

    self._parameterNode.EndModify(wasModified)


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
    stageNumber = int(self._parameterNode.GetParameter("CurrentStage"))

    stagesIterator = range(len(stagesList)) if self.ui.metricsTableWidget.linkStagesPushButton.checked else [stageNumber]
    for stageNumber in stagesIterator:
      stagesList[stageNumber]['metrics'] = self.ui.metricsTableWidget.getParametersFromGUI()

    stagesIterator = range(len(stagesList)) if self.ui.levelsTableWidget.linkStagesPushButton.checked else [stageNumber]
    for stageNumber in stagesIterator:
      stagesList[stageNumber]['levels'] = self.ui.levelsTableWidget.getParametersFromGUI()

    stagesIterator = range(len(stagesList)) if self.ui.linkMaskingStagesPushButton.checked else [stageNumber]
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
    if presetName == 'Load from preset':
      return
    presetParameters = self.logic.getPresetParametersByName(presetName)
    self._updatingGUIFromParameterNode = True
    self.ui.metricsTableWidget.linkStagesPushButton.checked = False
    self.ui.levelsTableWidget.linkStagesPushButton.checked = False
    self.ui.linkMaskingStagesPushButton.checked = False
    wasModified = self._parameterNode.StartModify()  # Modify in a single batch
    self._parameterNode.SetParameter("CurrentStage", "0")
    self._parameterNode.SetParameter("StagesJson", json.dumps(presetParameters['stages']))
    self._updatingGUIFromParameterNode = False
    self._parameterNode.EndModify(wasModified)

  def onRunRegistrationButton(self):
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

    parameters['initialTransformSettings'] = {}
    parameters['initialTransformSettings']['initializationFeature'] = int(self._parameterNode.GetParameter("initializationFeature"))
    parameters['initialTransformSettings']['initialTransformNode'] = self.ui.initialTransformNodeComboBox.currentNode()

    parameters['generalSettings'] = {}
    parameters['generalSettings']['dimensionality'] = self.ui.dimensionalitySpinBox.value
    parameters['generalSettings']['histogramMatching'] = int(self.ui.histogramMatchingCheckBox.checked)
    parameters['generalSettings']['winsorizeImageIntensities'] = [self.ui.winsorizeRangeWidget.minimumValue, self.ui.winsorizeRangeWidget.maximumValue]
    parameters['generalSettings']['computationPrecision'] = self.ui.computationPrecisionComboBox.currentText

    logLabelTimer = qt.QTimer()
    logLabelTimer.timeout.connect(lambda: self.ui.antsLogFittedText.setText(self.logic.antsLogLine))
    logLabelTimer.start(100)

    self.logic.process(**parameters)

    logLabelTimer.stop()
    self.ui.antsLogFittedText.setText(self.logic.antsLogLine)


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

    self.antsLogLine = ''
    self.tempDirectory = ''
    self.outputVolumeFileName = 'outputVolume.nii'
    self.outputTransformPrefix = 'outputTransform'
    executableExt = '.exe' if platform.system() == 'Windows' else ''
    self.antsRegistrationFileName = 'antsRegistration' + executableExt
    self.antsApplyTransformsFileName = 'antsApplyTransforms' + executableExt


  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    presetParameters = self.getPresetParametersByName()
    if not parameterNode.GetParameter("StagesJson"):
      parameterNode.SetParameter("StagesJson",  json.dumps(presetParameters["stages"]))
    if not parameterNode.GetParameter("CurrentStage"):
      parameterNode.SetParameter("CurrentStage", "0")

    if not parameterNode.GetParameter("OutputTransform"):
      parameterNode.SetParameter("OutputTransform", "")
    if not parameterNode.GetParameter("OutputVolume"):
      parameterNode.SetParameter("OutputVolume", "")
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


  def getPresetParametersByName(self, name='Rigid'):
    presetFilePath = os.path.join(os.path.dirname(__file__),'Resources','Presets', name + '.json')
    with open(presetFilePath) as presetFile:
      return json.load(presetFile)


  def process(self, stages, outputSettings, initialTransformSettings={}, generalSettings={}):
    """
    :param stages: list defining registration stages
    :param outputSettings: dictionary defining output settings
    :param initialTransformSettings: dictionary defining initial moving transform
    :param generalSettings: dictionary defining general registration settings
    See presets examples to see how these are specified
    """
    self.resetTempDirectory()

    initialTransformSettings['fixedImageNode'] = stages[0]['metrics'][0]['fixed']
    initialTransformSettings['movingImageNode'] = stages[0]['metrics'][0]['moving']

    antsRegistraionCommand = self.getAntsRegistrationCommand(stages, outputSettings, initialTransformSettings, generalSettings)
    self.runAntsCommand(self.antsRegistrationFileName, antsRegistraionCommand)

    if isinstance(outputSettings['transform'], slicer.vtkMRMLGridTransformNode):
      gridReferenceNode = stages[0]['metrics'][0]['fixed']
      antsApplyTransformsCommand = self.getAntsApplyTransformsCommand(gridReferenceNode)
      self.runAntsCommand(self.antsApplyTransformsFileName, antsApplyTransformsCommand)

    if outputSettings['transform'] is not None:
      self.loadOutputTransformNode(outputSettings['transform'])

    if outputSettings['volume'] is not None:
      self.loadOutputVolumeNode(outputSettings['volume'])

    self.resetTempDirectory()    

  def loadOutputTransformNode(self, outputTransformNode):
    fileExt = '.nii.gz' if isinstance(outputTransformNode, slicer.vtkMRMLGridTransformNode) else '.h5'
    outputTransformPath = os.path.join(self.getTempDirectory(), self.outputTransformPrefix + 'Composite' + fileExt)
    loadedOutputTransformNode = slicer.util.loadTransform(outputTransformPath)
    outputTransformNode.SetAndObserveTransformToParent(loadedOutputTransformNode.GetTransformToParent())
    slicer.mrmlScene.RemoveNode(loadedOutputTransformNode)

  def loadOutputVolumeNode(self, outputVolumeNode):
    outputVolumePath = os.path.join(self.getTempDirectory(), self.outputVolumeFileName)
    loadedOutputVolumeNode = slicer.util.loadVolume(outputVolumePath)
    outputVolumeNode.SetAndObserveImageData(loadedOutputVolumeNode.GetImageData())
    ijkToRas = vtk.vtkMatrix4x4()
    loadedOutputVolumeNode.GetIJKToRASMatrix(ijkToRas)
    outputVolumeNode.SetIJKToRASMatrix(ijkToRas)
    slicer.mrmlScene.RemoveNode(loadedOutputVolumeNode)

  def runAntsCommand(self, executableFileName, command):
    params = {}
    params['env'] = self.getAntsEnv()
    params['stdout'] = subprocess.PIPE
    params['universal_newlines'] = True
    if sys.platform == 'win32':
      params['startupinfo'] = self.getStartupInfo()

    executableFilePath = os.path.join(self.getAntsBinDir(), executableFileName)
    logging.info("Running ANTs Command: " + executableFilePath + " " + command)
    process = subprocess.Popen([executableFilePath] + command.split(" "), **params)

    for stdout_line in iter(process.stdout.readline, ""):
      self.antsLogLine = stdout_line.rstrip()
      logging.info(self.antsLogLine)
      slicer.app.processEvents()
    process.stdout.close()
    if process.wait():
      raise RuntimeError(executableFileName + " failed")

  def getStartupInfo(self):
    info = subprocess.STARTUPINFO()
    info.dwFlags = 1
    info.wShowWindow = 0
    return info

  def getAntsEnv(self):
    antsBinDir = self.getAntsBinDir()
    antsEnv = os.environ.copy()
    antsEnv["PATH"] = antsBinDir + os.pathsep + antsEnv["PATH"] if antsEnv.get("PATH") else antsBinDir
    return antsEnv

  def getAntsBinDir(self):
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
      antsExecutable = os.path.join(os.path.abspath(antsBinDirCandidate), self.antsRegistrationFileName)
      if os.path.isfile(antsExecutable):
        return os.path.abspath(antsBinDirCandidate)

    raise ValueError('ANTs not found')

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
    presetParameters = logic.getPresetParametersByName('QuickSyN')
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

