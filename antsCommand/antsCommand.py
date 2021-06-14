#!/usr/bin/env python-real

import os
import sys
import subprocess
import platform
import re


def runAntsCommand(antsExecutable, command, outputLogPath):
  executableFileName = getExecutableWithExtension(antsExecutable)
  executableFilePath = os.path.join(getAntsBinDir(), executableFileName)

  params = {}
  params['env'] = getAntsEnv()
  params['universal_newlines'] = True
  params['stdout'] = open(outputLogPath, "a")
  params['stderr'] = subprocess.STDOUT
  if sys.platform == 'win32':
    params['startupinfo'] = getStartupInfo()

  return subprocess.Popen([executableFilePath] + command.split(" "), **params)

def getStartupInfo():
  info = subprocess.STARTUPINFO()
  info.dwFlags = 1
  info.wShowWindow = 0
  return info

def getAntsEnv():
  antsBinDir = getAntsBinDir()
  antsEnv = os.environ.copy()
  antsEnv["PATH"] = antsBinDir + os.pathsep + antsEnv["PATH"] if antsEnv.get("PATH") else antsBinDir
  return antsEnv

def getAntsBinDir():
  scriptPath = os.path.dirname(os.path.abspath(__file__))
  antsBinDirCandidates = [
    os.path.join(scriptPath, '..'),
    os.path.join(scriptPath, '../bin'),
    os.path.join(scriptPath, '../../bin'),
    os.path.join(scriptPath, '../../../bin'),
    os.path.join(scriptPath, '../../../../bin'),
    os.path.join(scriptPath, '../../../../bin/Release'),
    os.path.join(scriptPath, '../../../../bin/Debug'),
    os.path.join(scriptPath, '../../../../../bin/Release'),
    os.path.join(scriptPath, '../../../../../bin/Debug') ]

  antsRegistrationFileName = getExecutableWithExtension('antsRegistration')
  for antsBinDirCandidate in antsBinDirCandidates:
    antsExecutable = os.path.join(os.path.abspath(antsBinDirCandidate), antsRegistrationFileName)
    if os.path.isfile(antsExecutable):
      return os.path.abspath(antsBinDirCandidate)

  raise ValueError('ANTs not found')

def getExecutableWithExtension(executableFileName):
  executableExt = '.exe' if platform.system() == 'Windows' else ''
  return executableFileName + executableExt


class CLIUpdater():
  def __init__(self, outputLogPath, antsCommand):
      self.logPath = outputLogPath
      self.convergence = self.getConvergenceFromCommand(antsCommand)
      self.totalLevels = len(self.convergence)
      self.currentStageDescription = ''
      self.currentLevel = 0
      self.currentIterNumber = 0

  def getConvergenceFromCommand(self, command):
    convergenceList = re.findall("(?<=convergence \[)[0-9x]+", command)
    if convergenceList:
      convergence = ('x'.join(convergenceList)).split('x')
      return [float(c) for c in convergence]
    return []

  def updateCLIStatus(self):
    with open(self.logPath) as f:
      lines = f.readlines()
      lastLine = lines[-1] if lines else ''
      text = ''.join(lines)
    self.updateProgress(text)
    self.updateStageProgress(lastLine)
    self.updateComment(text)

  def updateProgress(self, text):
    levelNumber = len(re.findall("DIAGNOSTIC,Iteration,metricValue,convergenceValue,ITERATION_TIME_INDEX,SINCE_LAST", text))
    if levelNumber != self.currentLevel:
      CLIUpdater.sendCLIProgress(levelNumber/self.totalLevels)
      self.currentLevel = levelNumber

  def updateStageProgress(self, lastLine):
    if re.search("[^X]DIAGNOSTIC.+", lastLine):
      iterNumber = int(lastLine.split(',')[1])
      if iterNumber != self.currentIterNumber:
        CLIUpdater.sendCLIStageProgress(iterNumber/max(1,self.convergence[self.currentLevel-1]))
        self.currentIterNumber = iterNumber

  def updateComment(self, text):
    stageDescriptionMatch = [''] + re.findall("(?<=[*]{3} )[a-zA-Z0-9 \-]+", text)
    stageDescription = stageDescriptionMatch[-1]
    if stageDescription != self.currentStageDescription:
      CLIUpdater.sendCLIComment(stageDescription)
      self.currentStageDescription = stageDescription

  @staticmethod
  def sendCLIProgress(percentage):
    print("<filter-progress>%f</filter-progress>" % percentage)
    sys.stdout.flush()

  @staticmethod
  def sendCLIStageProgress(percentage):
    print("<filter-stage-progress>%f</filter-stage-progress>" % percentage)
    sys.stdout.flush()

  @staticmethod
  def sendCLIComment(text):
    print("<filter-comment>%s</filter-comment>" % text)
    sys.stdout.flush()


if __name__ == "__main__":
  antsExecutable = sys.argv[-3]
  antsCommand = sys.argv[-2]
  outputLogPath = sys.argv[-1]

  CLIUpdater.sendCLIStageProgress(1)
  CLIUpdater.sendCLIComment(antsExecutable)

  process = runAntsCommand(antsExecutable, antsCommand, outputLogPath)

  if antsExecutable == 'antsRegistration':
    updater = CLIUpdater(outputLogPath, antsCommand)
    while process.poll() is None:
      updater.updateCLIStatus()
  else:
    process.wait()

  if process.returncode:
    raise subprocess.CalledProcessError(process.returncode, "ANTs")
