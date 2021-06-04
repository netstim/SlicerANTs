import qt
import os
import json
import glob

def saveStagesAsPreset(stages):
  from PythonQt import BoolResult
  ok = BoolResult()
  presetName = qt.QInputDialog().getText(qt.QWidget(), 'Save Preset', 'Preset name: ', qt.QLineEdit.Normal, 'my_preset', ok)
  if not ok:
    return
  if presetName in getPresetNames():
    qt.QMessageBox().warning(qt.QWidget(),'Warning', presetName + ' already exists. Set another name.')
    saveStagesAsPreset(stages)
    return
  outFilePath = os.path.join(getPresetsPath(), presetName + '.json')
  saveSettings = getPresetParametersByName()
  saveSettings['stages'] = removeNodesFromStages(stages)
  try:
    with open(outFilePath, 'w') as outfile:
      json.dump(saveSettings, outfile)
  except:
    qt.QMessageBox().warning(qt.QWidget(),'Warning', 'Unable to write into ' + outFilePath)
    return
  print('Saved preset to ' + outFilePath)
  return presetName

def removeNodesFromStages(stagesList):
  for stage in stagesList:
    for metric in stage['metrics']:
      metric['fixed'] = None
      metric['moving'] = None
    stage['masks']['fixed'] = None
    stage['masks']['moving'] = None

def getPresetParametersByName(name='Rigid'):
  presetFilePath = os.path.join(getPresetsPath(), name + '.json')
  with open(presetFilePath) as presetFile:
    return json.load(presetFile)

def getPresetNames():
  G = glob.glob(os.path.join(getPresetsPath(), '*.json'))
  return [os.path.splitext(os.path.basename(g))[0] for g in G]

def getPresetsPath():
  return os.path.join(os.path.dirname(__file__),'..','Resources','Presets')