#!/usr/bin/env python-real

import os
import sys
import logging
import subprocess
import platform


def runAntsCommand(executableFileName, command):
  params = {}
  params['env'] = getAntsEnv()
  params['stdout'] = subprocess.PIPE
  params['universal_newlines'] = True
  if sys.platform == 'win32':
    params['startupinfo'] = getStartupInfo()

  executableFilePath = os.path.join(getAntsBinDir(), executableFileName)
  return subprocess.Popen([executableFilePath] + command.split(" "), **params)

def logProcess(process):
  for stdout_line in iter(process.stdout.readline, ""):
    logging.info(stdout_line.rstrip())
  process.stdout.close()
  returnCode = process.wait()
  if returnCode:
    raise subprocess.CalledProcessError(returnCode, "ANTs")

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
    os.path.join(scriptPath, '../../../../bin/RelWithDebInfo'),
    os.path.join(scriptPath, '../../../../bin/MinSizeRel') ]

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
  antsExecutable = getExecutableWithExtension(sys.argv[-2])
  antsCommand = sys.argv[-1]
  process = runAntsCommand(antsExecutable, antsCommand)
  logProcess(process)
