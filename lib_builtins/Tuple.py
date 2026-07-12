def create(*items):
    return tuple(items)

def get(tpl, index):
    try: return tpl[int(index)]
    except: return None

def length(tpl): return len(tpl)
def to_list(tpl): return list(tpl)
def contains(tpl, item): return item in tpl
def index_of(tpl, item):
    try: return tpl.index(item)
    except: return -1