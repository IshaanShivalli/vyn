"""
List module for Vyn
"""

def create(*items):
    """Create a list with any number of items"""
    return list(items)

def append(lst, item):
    lst.append(item)
    return lst

def insert(lst, index, item):
    lst.insert(int(index), item)
    return lst

def remove(lst, item):
    if item in lst:
        lst.remove(item)
    return lst

def pop(lst, index=-1):
    try:
        return lst.pop(int(index))
    except:
        return None

def get(lst, index):
    try:
        return lst[int(index)]
    except:
        return None

def set_item(lst, index, value):
    try:
        lst[int(index)] = value
        return lst
    except:
        return lst

def length(lst):
    return len(lst)

def reverse(lst):
    lst.reverse()
    return lst

def sort(lst):
    try:
        lst.sort()
    except:
        pass
    return lst

def copy(lst):
    return lst[:]

def join(lst, separator=""):
    return separator.join(str(x) for x in lst)

def contains(lst, item):
    return item in lst

def clear(lst):
    lst.clear()
    return lst