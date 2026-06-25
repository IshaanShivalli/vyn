"""
random - Python's random module exposed flatly.
After `import random`:
    random()          → float between 0 and 1
    randint(a, b)
    choice(list)
    shuffle(list)
"""
import random as _random

def random():
    return _random.random()

def randint(a, b):
    return _random.randint(int(a), int(b))

def randrange(start, stop=None, step=1):
    if stop is None:
        return _random.randrange(int(start))
    return _random.randrange(int(start), int(stop), int(step))

def choice(seq):
    return _random.choice(seq)

def shuffle(seq):
    _random.shuffle(seq)
    return seq

def sample(seq, k):
    return _random.sample(seq, int(k))

def uniform(a, b):
    return _random.uniform(float(a), float(b))

def seed(s=None):
    _random.seed(s)
    return s