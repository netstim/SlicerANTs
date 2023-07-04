import os
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import json
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
    self.parent.title = "General Registration (ANTs)"
    self.parent.categories = ["Registration"]
    self.parent.associatedNodeTypes = ["vtkMRMLScriptedModuleNode"]
    self.parent.dependencies = ["antsRegistrationCLI"]
    self.parent.contributors = ["Simon Oxenford (Netstim Berlin)"]
    self.parent.helpText = """
See more information in <a href="https://github.com/netstim/SlicerANTs">module documentation</a>.
"""
    self.parent.acknowledgementText = "TODO"



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

  def setEditedNode(self, node, role='', context=''):
    self.setParameterNode(node)
    return node is not None

  def nodeEditable(self, node):
    return 0.7 if node is not None and node.GetAttribute('ModuleName') == self.moduleName else 0.0

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

    self.ui.parameterNodeSelector.addAttribute("vtkMRMLScriptedModuleNode", "ModuleName", self.moduleName)
    self.ui.parameterNodeSelector.setNodeTypeLabel("antsRegistrationParameters", "vtkMRMLScriptedModuleNode")

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

    self.ui.cliWidget = slicer.modules.antsregistrationcli.createNewWidgetRepresentation()
    self.layout.addWidget(self.ui.cliWidget.children()[3]) # progress bar
    self._cliObserver = None

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = antsRegistrationLogic()

    self.ui.stagesPresetsComboBox.addItems(['Select...'] + PresetManager().getPresetNames())
    self.ui.openPresetsDirectoryButton.clicked.connect(self.onOpenPresetsDirectoryButtonClicked)

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)


    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.parameterNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.setParameterNode)
    self.ui.stagesTableWidget.view.selectionModel().selectionChanged.connect(self.updateParameterNodeFromGUI)
    self.ui.outputInterpolationComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.outputTransformComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputVolumeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformTypeComboBox.connect("currentIndexChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.initialTransformNodeComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.dimensionalitySpinBox.connect("valueChanged(int)", self.updateParameterNodeFromGUI)
    self.ui.histogramMatchingCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.outputDisplacementFieldCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.winsorizeRangeWidget.connect("valuesChanged(double,double)", self.updateParameterNodeFromGUI)
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

    self.setParameterNode(self.logic.getParameterNode() if not self._parameterNode else self._parameterNode)

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

    wasBlocked = self.ui.parameterNodeSelector.blockSignals(True)
    self.ui.parameterNodeSelector.setCurrentNode(self._parameterNode)
    self.ui.parameterNodeSelector.blockSignals(wasBlocked)

    wasBlocked = self.ui.stagesPresetsComboBox.blockSignals(True)
    self.ui.stagesPresetsComboBox.setCurrentIndex(0)
    self.ui.stagesPresetsComboBox.blockSignals(wasBlocked)

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

    currentStage = int(self._parameterNode.GetParameter(self.logic.CURRENT_STAGE_PARAM))
    self.ui.stagesTableWidget.view.setCurrentIndex(self.ui.stagesTableWidget.model.index(currentStage, 0))
    self.ui.stagePropertiesCollapsibleButton.text = 'Stage ' + str(currentStage + 1) + ' Properties'
    self.updateStagesGUIFromParameter()

    self.ui.outputTransformComboBox.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.OUTPUT_TRANSFORM_REF))
    self.ui.outputVolumeComboBox.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.OUTPUT_VOLUME_REF))
    self.ui.outputInterpolationComboBox.currentText = self._parameterNode.GetParameter(self.logic.OUTPUT_INTERPOLATION_PARAM)
    self.ui.outputDisplacementFieldCheckBox.checked = int(self._parameterNode.GetParameter(self.logic.CREATE_DISPLACEMENT_FIELD_PARAM))

    self.ui.initialTransformTypeComboBox.currentIndex = int(self._parameterNode.GetParameter(self.logic.INITIALIZATION_FEATURE_PARAM)) + 2
    self.ui.initialTransformNodeComboBox.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.INITIAL_TRANSFORM_REF) if self.ui.initialTransformTypeComboBox.currentIndex == 1 else None)
    self.ui.initialTransformNodeComboBox.enabled = self.ui.initialTransformTypeComboBox.currentIndex == 1

    self.ui.dimensionalitySpinBox.value = int(self._parameterNode.GetParameter(self.logic.DIMENSIONALITY_PARAM))
    self.ui.histogramMatchingCheckBox.checked = int(self._parameterNode.GetParameter(self.logic.HISTOGRAM_MATCHING_PARAM))
    winsorizeIntensities = self._parameterNode.GetParameter(self.logic.WINSORIZE_IMAGE_INTENSITIES_PARAM).split(",")
    self.ui.winsorizeRangeWidget.setMinimumValue(float(winsorizeIntensities[0]))
    self.ui.winsorizeRangeWidget.setMaximumValue(float(winsorizeIntensities[1]))
    self.ui.computationPrecisionComboBox.currentText = self._parameterNode.GetParameter(self.logic.COMPUTATION_PRECISION_PARAM)

    self.ui.runRegistrationButton.enabled = self.ui.fixedImageNodeComboBox.currentNodeID and self.ui.movingImageNodeComboBox.currentNodeID and\
                                            (self.ui.outputTransformComboBox.currentNodeID or self.ui.outputVolumeComboBox.currentNodeID)

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateStagesGUIFromParameter(self):
    stagesList = json.loads(self._parameterNode.GetParameter(self.logic.STAGES_JSON_PARAM))
    self.ui.fixedImageNodeComboBox.setCurrentNodeID(stagesList[0]['metrics'][0]['fixed'])
    self.ui.movingImageNodeComboBox.setCurrentNodeID(stagesList[0]['metrics'][0]['moving'])
    self.setTransformsGUIFromList(stagesList)
    self.setCurrentStagePropertiesGUIFromList(stagesList)

  def setTransformsGUIFromList(self, stagesList):
    transformsParameters = [stage['transformParameters'] for stage in stagesList]
    self.ui.stagesTableWidget.setGUIFromParameters(transformsParameters)

  def setCurrentStagePropertiesGUIFromList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter(self.logic.CURRENT_STAGE_PARAM))
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

    self._parameterNode.SetParameter(self.logic.CURRENT_STAGE_PARAM, str(self.ui.stagesTableWidget.getSelectedRow()))

    self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_TRANSFORM_REF, self.ui.outputTransformComboBox.currentNodeID)
    self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_VOLUME_REF, self.ui.outputVolumeComboBox.currentNodeID)
    self._parameterNode.SetParameter(self.logic.OUTPUT_INTERPOLATION_PARAM, self.ui.outputInterpolationComboBox.currentText)
    self._parameterNode.SetParameter(self.logic.CREATE_DISPLACEMENT_FIELD_PARAM, str(int(self.ui.outputDisplacementFieldCheckBox.checked)))

    self._parameterNode.SetParameter(self.logic.INITIALIZATION_FEATURE_PARAM, str(self.ui.initialTransformTypeComboBox.currentIndex-2))
    self._parameterNode.SetNodeReferenceID(self.logic.INITIAL_TRANSFORM_REF, self.ui.initialTransformNodeComboBox.currentNodeID)

    self._parameterNode.SetParameter(self.logic.DIMENSIONALITY_PARAM, str(self.ui.dimensionalitySpinBox.value))
    self._parameterNode.SetParameter(self.logic.HISTOGRAM_MATCHING_PARAM, str(int(self.ui.histogramMatchingCheckBox.checked)))
    self._parameterNode.SetParameter(self.logic.WINSORIZE_IMAGE_INTENSITIES_PARAM,
                                     ",".join([str(self.ui.winsorizeRangeWidget.minimumValue),str(self.ui.winsorizeRangeWidget.maximumValue)]))
    self._parameterNode.SetParameter(self.logic.COMPUTATION_PRECISION_PARAM,  self.ui.computationPrecisionComboBox.currentText)

    self._parameterNode.EndModify(wasModified)


  def updateStagesFromFixedMovingNodes(self):
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    stagesList = json.loads(self._parameterNode.GetParameter(self.logic.STAGES_JSON_PARAM))
    for stage in stagesList:
      stage['metrics'][0]['fixed'] = self.ui.fixedImageNodeComboBox.currentNodeID
      stage['metrics'][0]['moving'] = self.ui.movingImageNodeComboBox.currentNodeID
    self._parameterNode.SetParameter(self.logic.STAGES_JSON_PARAM, json.dumps(stagesList))

  def updateStagesParameterFromGUI(self):
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    stagesList = json.loads(self._parameterNode.GetParameter(self.logic.STAGES_JSON_PARAM))
    self.setStagesTransformsToStagesList(stagesList)
    self.setCurrentStagePropertiesToStagesList(stagesList)
    self._parameterNode.SetParameter(self.logic.STAGES_JSON_PARAM, json.dumps(stagesList))

  def setStagesTransformsToStagesList(self, stagesList):
    for stageNumber,transformParameters in enumerate(self.ui.stagesTableWidget.getParametersFromGUI()):
      if stageNumber == len(stagesList):
        stagesList.append({})
      stagesList[stageNumber]['transformParameters'] = transformParameters

  def setCurrentStagePropertiesToStagesList(self, stagesList):
    currentStage = int(self._parameterNode.GetParameter(self.logic.CURRENT_STAGE_PARAM))

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
    stagesList = json.loads(self._parameterNode.GetParameter(self.logic.STAGES_JSON_PARAM))
    if len(stagesList) == 1:
      return
    currentStage = int(self._parameterNode.GetParameter(self.logic.CURRENT_STAGE_PARAM))
    stagesList.pop(currentStage)
    wasModified = self._parameterNode.StartModify()  # Modify in a single batch
    self._parameterNode.SetParameter(self.logic.CURRENT_STAGE_PARAM, str(max(currentStage-1,0)))
    self._parameterNode.SetParameter(self.logic.STAGES_JSON_PARAM, json.dumps(stagesList))
    self._parameterNode.EndModify(wasModified)

  def onPresetSelected(self, presetName):
    if presetName == 'Select...' or self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    wasModified = self._parameterNode.StartModify()  # Modify in a single batch
    presetParameters = PresetManager().getPresetParametersByName(presetName)
    for stage in presetParameters['stages']:
      stage['metrics'][0]['fixed'] = self.ui.fixedImageNodeComboBox.currentNodeID
      stage['metrics'][0]['moving'] = self.ui.movingImageNodeComboBox.currentNodeID
    self._parameterNode.SetParameter(self.logic.STAGES_JSON_PARAM, json.dumps(presetParameters['stages']))
    self._parameterNode.SetParameter(self.logic.CURRENT_STAGE_PARAM, "0")
    self._parameterNode.EndModify(wasModified)

  def onSavePresetPushButton(self):
    stages = json.loads(self._parameterNode.GetParameter(self.logic.STAGES_JSON_PARAM))
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

    parameters = self.logic.createProcessParameters(self._parameterNode)
    self.logic.process(**parameters)

    self.ui.cliWidget.setCurrentCommandLineModuleNode(self.logic.cliNode)
    self._cliObserver = self.logic.cliNode.AddObserver('ModifiedEvent', self.onProcessingStatusUpdate)
    self.ui.runRegistrationButton.text = 'Cancel'

  def onProcessingStatusUpdate(self, caller, event):
    if caller.GetStatus() & caller.Cancelled:
      self.ui.runRegistrationButton.text = "Run Registration"
      self.logic.cliNode.RemoveObserver(self._cliObserver)
    elif caller.GetStatus() & caller.Completed:
      if caller.GetStatus() & caller.ErrorsMask:
        qt.QMessageBox().warning(qt.QWidget(),'Error', 'ANTs Failed. See CLI output.')
      self.ui.runRegistrationButton.text = "Run Registration"
      self.logic.cliNode.RemoveObserver(self._cliObserver)
    else:
      self.ui.runRegistrationButton.text = "Cancel"

  def onOpenPresetsDirectoryButtonClicked(self):
    import platform, subprocess
    presetPath = PresetManager().presetPath
    if platform.system() == "Windows":
      os.startfile(presetPath)
    elif platform.system() == "Darwin":
      subprocess.Popen(["open", presetPath])
    else:
      subprocess.Popen(["xdg-open", presetPath])


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

  OUTPUT_TRANSFORM_REF = "OutputTransform"
  OUTPUT_VOLUME_REF = "OutputVolume"
  INITIAL_TRANSFORM_REF = "InitialTransform"
  OUTPUT_INTERPOLATION_PARAM = "OutputInterpolation"
  STAGES_JSON_PARAM = "StagesJson"
  CURRENT_STAGE_PARAM = "CurrentStage"
  CREATE_DISPLACEMENT_FIELD_PARAM = "OutputDisplacementField"
  INITIALIZATION_FEATURE_PARAM = "initializationFeature"
  DIMENSIONALITY_PARAM = "Dimensionality"
  HISTOGRAM_MATCHING_PARAM = "HistogramMatching"
  WINSORIZE_IMAGE_INTENSITIES_PARAM = "WinsorizeImageIntensities"
  COMPUTATION_PRECISION_PARAM = "ComputationPrecision"

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

    self.cliNode = None
    self._cliParams = {}

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    presetParameters = PresetManager().getPresetParametersByName()
    if not parameterNode.GetParameter(self.STAGES_JSON_PARAM):
      parameterNode.SetParameter(self.STAGES_JSON_PARAM,  json.dumps(presetParameters["stages"]))
    if not parameterNode.GetParameter(self.CURRENT_STAGE_PARAM):
      parameterNode.SetParameter(self.CURRENT_STAGE_PARAM, "0")

    if not parameterNode.GetNodeReference(self.OUTPUT_TRANSFORM_REF):
      parameterNode.SetNodeReferenceID(self.OUTPUT_TRANSFORM_REF, "")
    if not parameterNode.GetNodeReference(self.OUTPUT_VOLUME_REF):
      parameterNode.SetNodeReferenceID(self.OUTPUT_VOLUME_REF, "")
    if not parameterNode.GetParameter(self.OUTPUT_INTERPOLATION_PARAM):
      parameterNode.SetParameter(self.OUTPUT_INTERPOLATION_PARAM, str(presetParameters["outputSettings"]["interpolation"]))
    if not parameterNode.GetParameter(self.CREATE_DISPLACEMENT_FIELD_PARAM):
      parameterNode.SetParameter(self.CREATE_DISPLACEMENT_FIELD_PARAM, "0")

    if not parameterNode.GetParameter(self.INITIALIZATION_FEATURE_PARAM):
      parameterNode.SetParameter(self.INITIALIZATION_FEATURE_PARAM, str(presetParameters["initialTransformSettings"]["initializationFeature"]))
    if not parameterNode.GetNodeReference(self.INITIAL_TRANSFORM_REF):
      parameterNode.SetNodeReferenceID(self.INITIAL_TRANSFORM_REF, "")

    if not parameterNode.GetParameter(self.DIMENSIONALITY_PARAM):
      parameterNode.SetParameter(self.DIMENSIONALITY_PARAM, str(presetParameters["generalSettings"]["dimensionality"]))
    if not parameterNode.GetParameter(self.HISTOGRAM_MATCHING_PARAM):
      parameterNode.SetParameter(self.HISTOGRAM_MATCHING_PARAM, str(presetParameters["generalSettings"]["histogramMatching"]))
    if not parameterNode.GetParameter(self.WINSORIZE_IMAGE_INTENSITIES_PARAM):
      parameterNode.SetParameter(self.WINSORIZE_IMAGE_INTENSITIES_PARAM, ",".join([str(x) for x in presetParameters["generalSettings"]["winsorizeImageIntensities"]]))
    if not parameterNode.GetParameter(self.COMPUTATION_PRECISION_PARAM):
      parameterNode.SetParameter(self.COMPUTATION_PRECISION_PARAM, presetParameters["generalSettings"]["computationPrecision"])

  def cancelRegistration(self):
    if self.cliNode:
      self.cliNode.Cancel()

  def createProcessParameters(self, paramNode):
    parameters = {}
    parameters['stages'] = json.loads(paramNode.GetParameter(self.STAGES_JSON_PARAM))

    # ID to Node
    for stage in parameters['stages']:
      for metric in stage['metrics']:
        metric['fixed'] = slicer.util.getNode(metric['fixed']) if metric['fixed'] else ''
        metric['moving'] = slicer.util.getNode(metric['moving']) if metric['moving'] else ''
      stage['masks']['fixed'] = slicer.util.getNode(stage['masks']['fixed']) if stage['masks']['fixed'] else ''
      stage['masks']['moving'] = slicer.util.getNode(stage['masks']['moving']) if stage['masks']['moving'] else ''

    parameters['outputSettings'] = {}
    parameters['outputSettings']['transform'] = paramNode.GetNodeReference(self.OUTPUT_TRANSFORM_REF)
    parameters['outputSettings']['volume'] = paramNode.GetNodeReference(self.OUTPUT_VOLUME_REF)
    parameters['outputSettings']['interpolation'] = paramNode.GetParameter(self.OUTPUT_INTERPOLATION_PARAM)
    parameters['outputSettings']['useDisplacementField'] = int(paramNode.GetParameter(self.CREATE_DISPLACEMENT_FIELD_PARAM))

    parameters['initialTransformSettings'] = {}
    parameters['initialTransformSettings']['initializationFeature'] = int(paramNode.GetParameter(self.INITIALIZATION_FEATURE_PARAM))
    parameters['initialTransformSettings']['initialTransformNode'] = paramNode.GetNodeReference(self.INITIAL_TRANSFORM_REF)

    parameters['generalSettings'] = {}
    parameters['generalSettings']['dimensionality'] = int(paramNode.GetParameter(self.DIMENSIONALITY_PARAM))
    parameters['generalSettings']['histogramMatching'] = int(paramNode.GetParameter(self.HISTOGRAM_MATCHING_PARAM))
    parameters['generalSettings']['winsorizeImageIntensities'] = \
      [float(val) for val in paramNode.GetParameter(self.WINSORIZE_IMAGE_INTENSITIES_PARAM).split(',')]
    parameters['generalSettings']['computationPrecision'] = paramNode.GetParameter(self.COMPUTATION_PRECISION_PARAM)

    return parameters

  def process(self, stages, outputSettings, initialTransformSettings=None, generalSettings=None, wait_for_completion=False):
    """
    :param stages: list defining registration stages
    :param outputSettings: dictionary defining output settings
    :param initialTransformSettings: dictionary defining initial moving transform
    :param generalSettings: dictionary defining general registration settings
    :param wait_for_completion: flag to enable waiting for completion
    See presets examples to see how these are specified
    """

    if generalSettings is None:
      generalSettings = {}
    if initialTransformSettings is None:
      initialTransformSettings = {}
    initialTransformSettings['fixedImageNode'] = stages[0]['metrics'][0]['fixed']
    initialTransformSettings['movingImageNode'] = stages[0]['metrics'][0]['moving']

    self._cliParams = {}
    self.getOrSetCLIParam(stages[0]['metrics'][0]['fixed']) # put in first position. will be used as reference in cli
    self._cliParams["antsCommand"] = self.getAntsRegistrationCommand(stages, outputSettings, initialTransformSettings, generalSettings)

    if outputSettings["transform"] is not None:
      if ("useDisplacementField" in outputSettings) and outputSettings["useDisplacementField"]:
        self._cliParams["outputDisplacementField"] = outputSettings["transform"]
      else:
        self._cliParams["outputCompositeTransform"] = outputSettings["transform"]
    
    self._cliParams["useFloat"] = (generalSettings["computationPrecision"]  == "float")

    self.cliNode = slicer.cli.run(slicer.modules.antsregistrationcli, None, self._cliParams,
                                  wait_for_completion=wait_for_completion, update_display=False)

  def getAntsRegistrationCommand(self, stages, outputSettings, initialTransformSettings=None, generalSettings=None):
    if generalSettings is None:
      generalSettings = {}
    if initialTransformSettings is None:
      initialTransformSettings = {}
    antsCommand = self.getGeneralSettingsCommand(**generalSettings)
    antsCommand = antsCommand + self.getOutputCommand(interpolation=outputSettings['interpolation'], volume=outputSettings['volume'])
    antsCommand = antsCommand + self.getInitialMovingTransformCommand(**initialTransformSettings)
    for stage in stages:
      antsCommand = antsCommand + self.getStageCommand(**stage)
    return antsCommand

  def getGeneralSettingsCommand(self, dimensionality=3, histogramMatching=False, winsorizeImageIntensities=None, computationPrecision="float"):
    if winsorizeImageIntensities is None:
      winsorizeImageIntensities = [0, 1]
    command = "--dimensionality %i" % dimensionality
    command = command + " --use-histogram-matching %i" % histogramMatching
    command = command + " --winsorize-image-intensities [%.3f,%.3f]" % tuple(winsorizeImageIntensities)
    command = command + " --float $useFloat"
    command = command + " --verbose 1"
    return command

  def getOutputCommand(self, interpolation='Linear', volume=None):
    command = " --interpolation %s" % interpolation
    if volume is not None:
      command = command + " --output [%s,%s]" % ("$outputBase", self.getOrSetCLIParam(volume, "outputVolume"))
    else:
      command = command + " --output $outputBase"
    command = command + " --write-composite-transform 1"
    command = command + " --collapse-output-transforms 1"
    return command

  def getInitialMovingTransformCommand(self, initialTransformNode=None, initializationFeature=-1, fixedImageNode=None, movingImageNode=None):
    if initialTransformNode is not None:
      return " --initial-moving-transform %s" % self.getOrSetCLIParam(initialTransformNode, "inputTransform")
    elif initializationFeature >= 0:
      return " --initial-moving-transform [%s,%s,%i]" % (self.getOrSetCLIParam(fixedImageNode), self.getOrSetCLIParam(movingImageNode), initializationFeature)
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
    return " --metric %s[%s,%s,%s]" % (type, self.getOrSetCLIParam(fixed), self.getOrSetCLIParam(moving), settings)

  def getMasksCommand(self, fixed=None, moving=None):
    fixedMask = self.getOrSetCLIParam(fixed) if fixed else ''
    movingMask = self.getOrSetCLIParam(moving) if moving else ''
    if fixedMask and movingMask:
      return " --masks [%s,%s]" % (fixedMask, movingMask)
    return ""

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

  def getOrSetCLIParam(self, mrmlNode, cliparam="inputVolume"):
    greatestInputVolume = 0
    nodeID = mrmlNode.GetID()
    # get part
    for key,val in self._cliParams.items():
      if key.startswith(cliparam) and nodeID == val:
        return "$" + key
      elif key.startswith("inputVolume"):
        greatestInputVolume = int(key[-2:])
    # set part
    if cliparam == "inputVolume":
      cliparam = "inputVolume%02i" % (greatestInputVolume+1)
    self._cliParams[cliparam] = nodeID
    return "$" + cliparam


#
# Preset Manager
#

class PresetManager:
  def __init__(self):
      self.presetPath = os.path.join(os.path.dirname(__file__), 'Resources', 'Presets')

  def saveStagesAsPreset(self, stages):
    from PythonQt import BoolResult
    ok = BoolResult()
    presetName = \
      qt.QInputDialog().getText(qt.QWidget(), 'Save Preset', 'Preset name: ', qt.QLineEdit.Normal, 'my_preset', ok)
    if not ok:
      return
    if presetName in self.getPresetNames():
      slicer.util.warningDisplay(f'{presetName} already exists. Set another name.')
      return self.saveStagesAsPreset(stages)
    outFilePath = os.path.join(self.presetPath, f'{presetName}.json')
    saveSettings = self.getPresetParametersByName()
    saveSettings['stages'] = stages
    try:
      with open(outFilePath, 'w') as outfile:
        json.dump(saveSettings, outfile)
    except:
      slicer.util.warningDisplay(f'Unable to write into {outFilePath}')
      return
    slicer.util.infoDisplay(f'Saved preset to {outFilePath}.')
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
    fixed = sampleDataLogic.downloadMRBrainTumor1()
    moving = sampleDataLogic.downloadMRBrainTumor2()

    outputVolume = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')

    logic = antsRegistrationLogic()
    presetParameters = PresetManager().getPresetParametersByName('QuickSyN')
    for stage in presetParameters['stages']:
      for metric in stage['metrics']:
        metric['fixed'] = fixed
        metric['moving'] = moving
      # let's make it quick
      for step in stage['levels']['steps']:
        step['shrinkFactors'] = 10
      stage['levels']['convergenceThreshold'] = 1
      stage['levels']['convergenceWindowSize'] = 5

    presetParameters['outputSettings']['volume'] = outputVolume
    presetParameters['outputSettings']['transform'] = None
    presetParameters['outputSettings']['log'] = None

    logic.process(**presetParameters)

    logic.cliNode.AddObserver('ModifiedEvent', self.onProcessingStatusUpdate)

  def onProcessingStatusUpdate(self, caller, event):
    if caller.GetStatus() & caller.Completed:
      self.delayDisplay('Test passed!')
