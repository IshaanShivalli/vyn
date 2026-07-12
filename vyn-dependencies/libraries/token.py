"""
token - Secure random token generation via secrets
Usage: import token
"""
import secrets
import string

def generateToken(nbytes=32):
    return secrets.token_hex(int(nbytes))

def generateUrlToken(nbytes=32):
    return secrets.token_urlsafe(int(nbytes))

def generatePin(length=6):
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(int(length)))

def generatePassword(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(int(length)))

def compareTokens(a, b):
    return secrets.compare_digest(str(a), str(b))