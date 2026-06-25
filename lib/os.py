"""
os.vyn implementation as real Python library.
"""
import os as _os
import shutil
import tempfile


def getcwd():
    return _os.getcwd()


def chdir(path):
    return _os.chdir(path)


def listFiles(path):
    return _os.listdir(path)


def fileExists(path):
    return _os.path.exists(path)


def mkdir(path):
    return _os.mkdir(path)


def rmdir(path):
    return _os.rmdir(path)


def removeFile(path):
    return _os.remove(path)


def copyFile(src, dest):
    return shutil.copy(src, dest)


def renameFile(oldName, newName):
    return _os.rename(oldName, newName)


def getEnv(varName):
    return _os.getenv(varName)


def setEnv(varName, value):
    _os.environ[varName] = value
    return value


def getHomeDir():
    return _os.path.expanduser("~")


def getTempDir():
    return tempfile.gettempdir()


def pathSeparator():
    return _os.sep


def getPathExists(path):
    return _os.path.exists(path)


def isFile(path):
    return _os.path.isfile(path)


def isDir(path):
    return _os.path.isdir(path)


def getFileSize(path):
    return _os.path.getsize(path)


def getFileModTime(path):
    return _os.path.getmtime(path)
