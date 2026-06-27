"""
uuid - Unique ID generation
Usage: import uuid
"""
import uuid as _uuid

def uuidv4():
    return str(_uuid.uuid4())

def uuidv1():
    return str(_uuid.uuid1())

def isValid(uid):
    try:
        _uuid.UUID(str(uid))
        return True
    except ValueError:
        return False