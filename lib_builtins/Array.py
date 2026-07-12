def create(size, default=None):
    return [default] * int(size)

def get(arr, index):
    try: return arr[int(index)]
    except: return None

def set_item(arr, index, value):
    try:
        arr[int(index)] = value
        return arr
    except:
        return arr

def length(arr): return len(arr)
def fill(arr, value):
    for i in range(len(arr)): arr[i] = value
    return arr