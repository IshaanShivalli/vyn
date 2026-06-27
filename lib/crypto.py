"""
crypto - Hashing via hashlib
Usage: import crypto
"""
import hashlib

def md5(text):
    return hashlib.md5(str(text).encode()).hexdigest()

def sha256(text):
    return hashlib.sha256(str(text).encode()).hexdigest()

def sha512(text):
    return hashlib.sha512(str(text).encode()).hexdigest()

def sha1(text):
    return hashlib.sha1(str(text).encode()).hexdigest()

def verify(text, hash_value, algorithm="sha256"):
    algos = {"md5": md5, "sha1": sha1, "sha256": sha256, "sha512": sha512}
    if algorithm not in algos:
        return False
    return algos[algorithm](text) == hash_value