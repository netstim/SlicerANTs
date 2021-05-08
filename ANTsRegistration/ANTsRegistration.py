import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import PythonQt
import platform
import json
from Widgets.util import StagesTable, MetricsTable, LevelsTable


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
    self.ui.outputVolumeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformTypeComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformFixedNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformMovingNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.dimensionalitySpinBox.connect("valueChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.histogramMatchingCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.winsorizeRangeWidget.connect("rangeChanged(double,double)", self.updateParameterNodeFromGUI)
    self.ui.floatComputationCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)

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

    # Buttons
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

    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    self.ui.stagesTableWidget.view.setCurrentIndex(self.ui.stagesTableWidget.model.index(currentStage, 0))
    self.ui.stagePropertiesCollapsibleButton.text = 'Stage ' + str(currentStage + 1) + ' Properties'
    self.updateStagesGUIFromParameter()

    self.ui.outputInterpolationComboBox.currentText = self._parameterNode.GetParameter("OutputInterpolation")
    self.ui.outputVolumeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))

    self.ui.initialTransformTypeComboBox.currentText = self._parameterNode.GetParameter("InitialTransformType")
    self.ui.initialTransformNodeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("InitialTransform"))
    self.ui.initialTransformFixedNodeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("InitialTransformFixed"))
    self.ui.initialTransformMovingNodeComboBox.setCurrentNode(self._parameterNode.GetNodeReference("InitialTransformMoving"))

    self.ui.initialTransformNodeComboBox.enabled = self.ui.initialTransformTypeComboBox.currentIndex == 1
    self.ui.initialTransformFixedNodeComboBox.enabled = self.ui.initialTransformTypeComboBox.currentIndex > 1
    self.ui.initialTransformMovingNodeComboBox.enabled = self.ui.initialTransformTypeComboBox.currentIndex > 1

    self.ui.dimensionalitySpinBox.value = int(self._parameterNode.GetParameter("Dimensionality"))
    self.ui.histogramMatchingCheckBox.checked = int(self._parameterNode.GetParameter("HistogramMatching"))
    self.ui.winsorizeRangeWidget.setMinimumValue(float(self._parameterNode.GetParameter("WinsorizeImageIntensities").split(",")[0]))
    self.ui.winsorizeRangeWidget.setMaximumValue(float(self._parameterNode.GetParameter("WinsorizeImageIntensities").split(",")[1]))
    self.ui.floatComputationCheckBox.checked = int(self._parameterNode.GetParameter("FloatComputation"))

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateStagesGUIFromParameter(self):
    stagesList = json.loads(self._parameterNode.GetParameter("StagesJson"))
    self.setTransformsGUIFromList(stagesList)
    self.setCurrentStagePropertiesGUIFromList(stagesList)

  def setTransformsGUIFromList(self, stagesList):
    transformsParameters = [stage['transform'] for stage in stagesList]
    self.ui.stagesTableWidget.setGUIFromParameters(transformsParameters)

  def setCurrentStagePropertiesGUIFromList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    if 'metrics' in stagesList[currentStage].keys():
      self.ui.metricsTableWidget.setGUIFromParameters(stagesList[currentStage]['metrics'])
      self.ui.levelsTableWidget.setGUIFromParameters(stagesList[currentStage]['levels'])
      self.ui.fixedMaskComboBox.setCurrentNodeID(stagesList[currentStage]['masking']['fixed'])
      self.ui.movingMaskComboBox.setCurrentNodeID(stagesList[currentStage]['masking']['moving'])


  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetParameter("CurrentStage", str(self.ui.stagesTableWidget.getSelectedRow()))
    
    self._parameterNode.SetParameter("OutputInterpolation", self.ui.outputInterpolationComboBox.currentText)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputVolumeComboBox.currentNodeID)

    self._parameterNode.SetParameter("InitialTransformType", self.ui.initialTransformTypeComboBox.currentText)
    self._parameterNode.SetNodeReferenceID("InitialTransform", self.ui.initialTransformNodeComboBox.currentNodeID)
    self._parameterNode.SetNodeReferenceID("InitialTransformFixed", self.ui.initialTransformFixedNodeComboBox.currentNodeID)
    self._parameterNode.SetNodeReferenceID("InitialTransformMoving", self.ui.initialTransformMovingNodeComboBox.currentNodeID)

    self._parameterNode.SetParameter("Dimensionality", str(self.ui.dimensionalitySpinBox.value))
    self._parameterNode.SetParameter("HistogramMatching", str(int(self.ui.histogramMatchingCheckBox.checked)))
    self._parameterNode.SetParameter("WinsorizeImageIntensities", ",".join([str(self.ui.winsorizeRangeWidget.minimumValue),str(self.ui.winsorizeRangeWidget.maximumValue)]))
    self._parameterNode.SetParameter("FloatComputation",  str(int(self.ui.floatComputationCheckBox.checked)))

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
      stagesList[stageNumber]['transform'] = transformParameters

  def setCurrentStagePropertiesToStagesList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter("CurrentStage"))
    stagesList[currentStage]['metrics'] = self.ui.metricsTableWidget.getParametersFromGUI()
    stagesList[currentStage]['levels'] = self.ui.levelsTableWidget.getParametersFromGUI()
    stagesList[currentStage]['masking'] = {'fixed': self.ui.fixedMaskComboBox.currentNodeID, 'moving': self.ui.movingMaskComboBox.currentNodeID}

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



  def onRunRegistrationButton(self):
    parameters = {}
    parameters['stages'] = self._parameterNode.GetParameter("StagesJson")


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
      import Widgets
      import Widgets.util
      importlib.reload(Widgets.util)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    presetParameters = self.getPresetParameters()
    if not parameterNode.GetParameter("StagesJson"):
      parameterNode.SetParameter("StagesJson",  json.dumps(presetParameters["stages"]))
    if not parameterNode.GetParameter("CurrentStage"):
      parameterNode.SetParameter("CurrentStage", "0")

    if not parameterNode.GetParameter("OutputInterpolation"):
      parameterNode.SetParameter("OutputInterpolation", str(presetParameters["outputInterpolation"]))
    if not parameterNode.GetParameter("OutputVolume"):
      parameterNode.SetParameter("OutputVolume", "")

    if not parameterNode.GetParameter("InitialTransformType"):
      parameterNode.SetParameter("InitialTransformType", str(presetParameters["initialTransformType"]))
    if not parameterNode.GetParameter("InitialTransformFixed"):
      parameterNode.SetParameter("InitialTransformFixed", "")
    if not parameterNode.GetParameter("InitialTransformMoving"):
      parameterNode.SetParameter("InitialTransformFixed", "")
    if not parameterNode.GetParameter("InitialTransform"):
      parameterNode.SetParameter("InitialTransform", "")

    if not parameterNode.GetParameter("Dimensionality"):
      parameterNode.SetParameter("Dimensionality", str(presetParameters["dimensionality"]))
    if not parameterNode.GetParameter("HistogramMatching"):
      parameterNode.SetParameter("HistogramMatching", str(presetParameters["histogramMatching"]))
    if not parameterNode.GetParameter("WinsorizeImageIntensities"):
      parameterNode.SetParameter("WinsorizeImageIntensities", str(presetParameters["winsorizeImageIntensities"]))
    if not parameterNode.GetParameter("FloatComputation"):
      parameterNode.SetParameter("FloatComputation", str(presetParameters["floatComputation"]))


  def getPresetParameters(self):
    presetFilePath = os.path.join(os.path.dirname(__file__),'Resources','Presets','basicRigid.json')
    with open(presetFilePath) as presetFile:
      return json.load(presetFile)

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

  def process(self, stages, outputs, initialMovingTransform={}, generalSettings={}):
    """
    :param stages: list defining registration stages
    :param outputs: dictionary defining output settings
    :param initialMovingTransform: dictionary defining initial moving transform
    :param generalSettings: dictionary defining general registration settings
    See presets examples to see how these are specified
    """


    antsCommand = self.getGeneralSettingsCommand(**generalSettings)
    antsCommand = antsCommand + " " + self.getOutputCommand(interpolation=outputs['outputInterpolation'])
    antsCommand = antsCommand + " " + self.getInitialMovingTransformCommand(**initialMovingTransform)
    for stage in stages:
      antsCommand = antsCommand + " " + self.getStageCommand(**stage)

    import time
    startTime = time.time()
    logging.info('Processing started')


    stopTime = time.time()
    logging.info('Processing completed in {0:.2f} seconds'.format(stopTime-startTime))


  def getGeneralSettingsCommand(self, dimensionality=3, histogramMatching=False, winsorizeImageIntensities=(0,1), floatComputation=False):
    command = "--dimensionality %i" % dimensionality
    command = command + " --use-histogram-matching %i" % histogramMatching
    command = command + " --winsorize-image-intensities [%.3f,%.3f]" % winsorizeImageIntensities
    command = command + " --float %i" % floatComputation
    return command

  def getOutputCommand(self, interpolation='Linear'):
    command = "--interpolation %s" % interpolation
    command = command + " --output [%s,%s]" % os.path.join(self.getTempDirectory(), 'output'), os.path.join(self.getTempDirectory(), 'warpedImage.nii')
    command = command + " --write-composite-transform 1"
    command = command + " --collapse-output-transforms 1"
    return command

  def getInitialMovingTransformCommand(self, initialTransformNode=None, initializationFeature=None, fixedImageNode=None, movingImageNode=None):
    if initialTransformNode is not None:
      return "--initialTransform %s" % self.saveNodeAndGetPath(initialTransformNode)
    elif initializationFeature is not None:
      return "--initialTransform [%s,%s,%i]" % self.saveNodeAndGetPath(fixedImageNode), self.saveNodeAndGetPath(movingImageNode), initializationFeature
    else:
      return ""

  def getStageCommand(self, transform, metrics, levels, masks):
    command = self.getTransformCommand(**transform)
    for metric in metrics:
      command = command + " " + self.getMetricCommand(**metric)
    command = command + " " + self.getLevelsCommand(**levels)
    command = command + " " + self.getMasksCommand(**masks)

  def getTransformCommand(self, transformType, settingsString):
    return "--transform %s[%s]" % transformType, settingsString

  def getMetricCommand(self, metricType, fixedImageNode, movingImageNode, settingsString):
    return "--metric %s[%s,%s,%s]" % metricType, self.saveNodeAndGetPath(fixedImageNode), self.saveNodeAndGetPath(movingImageNode), settingsString

  def getMasksCommand(self, fixedMaskNode=None, movingMaskNode=None):
    fixedMask = self.saveNodeAndGetPath(fixedMaskNode) if fixedMaskNode else 'NULL'
    movingMask = self.saveNodeAndGetPath(movingMaskNode) if movingMaskNode else 'NULL'
    return " --masks [%s,%s]" % fixedMask, movingMask

  def getLevelsCommand(self, steps, convergenceThreshold, convergenceWindowSize, smoothingSigmasUnit):
    convergence = self.joinStepsInfoForKey(steps, 'convergence')
    smoothingSigmas = self.joinStepsInfoForKey(steps, 'smoothingSigmas')
    shrinkFactors = self.joinStepsInfoForKey(steps, 'shrinkFactors')
    command = "--convergence [%s,1e-%i,%i]" % convergence, convergenceThreshold, convergenceWindowSize
    command = command + " --smoothing-sigmas %s%s" % smoothingSigmas, smoothingSigmasUnit
    command = command + "  --shrink-factors %s" % shrinkFactors
    return command

  def joinStepsInfoForKey(self, steps, key):
    out = [str(step[key]) for step in steps]
    return "x".join(out)

  def saveNodeAndGetPath(self, node):
    # New location definition
    fileExtension = '.nii' if isinstance(node, slicer.vtkMRMLVolumeNode) else '.h5'
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

  def getTempDirectory(self):
    tempDir = qt.QDir(self.getTempDirectoryBase())
    tempDirName = qt.QDateTime().currentDateTime().toString("yyyyMMdd_hhmmss_zzz")
    fileInfo = qt.QFileInfo(qt.QDir(tempDir), tempDirName)
    dirPath = fileInfo.absoluteFilePath()
    qt.QDir().mkpath(dirPath)
    return dirPath

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

