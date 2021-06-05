#!/usr/bin/env python-real

import os
import sys
import subprocess
import platform


def runAntsCommand(executableFileName, command, outputLogPath):
  executableFilePath = os.path.join(getAntsBinDir(), executableFileName)

  params = {}
  params['env'] = getAntsEnv()
  params['universal_newlines'] = True
  try:
    f = open(outputLogPath, "a")
    f.write(executableFilePath + ' ' + command + '\n\n')
    params['stdout'] = f
    params['stderr'] = subprocess.STDOUT
  except:
    params['stdout'] = subprocess.PIPE
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

if __name__ == "__main__":
  antsExecutable = getExecutableWithExtension(sys.argv[-3])
  antsCommand = sys.argv[-2]
  outputLogPath = sys.argv[-1]
  process = runAntsCommand(antsExecutable, antsCommand, outputLogPath)
  process.wait()
  if process.returncode:
    raise subprocess.CalledProcessError(process.returncode, "ANTs")
    
