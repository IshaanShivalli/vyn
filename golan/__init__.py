"""Golan language support package for PL."""

from .syntax import register_syntax, parse_go_function_header

__all__ = [
    'register_syntax',
    'parse_go_function_header',
]
