"""
sys.vyn implementation as real Python library.
"""
import sys as _sys
import os as _os
import time as _time
import subprocess


def exit(code=0):
    return _sys.exit(code)


def getVersion():
    return _sys.version


def getPlatform():
    return _sys.platform


def getArguments():
    return list(_sys.argv)


def getEnvironment():
    return dict(_os.environ)


def getPath():
    return list(_sys.path)


def getModules():
    return list(_sys.modules.keys())


def getMemoryInfo():
    return "N/A"


def getCurrentDir():
    return _os.getcwd()


def setCurrentDir(path):
    return _os.chdir(path)


def sleep(milliseconds):
    _time.sleep(milliseconds / 1000.0)
    return milliseconds


def getTime():
    return int(_time.time() * 1000)


def executeCommand(command):
    return subprocess.getoutput(command)


def getUsername():
    return _os.getenv("USERNAME") or _os.getenv("USER") or "unknown"
