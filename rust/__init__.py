"""Compatibility layer for the Vyn Rust-backed result helpers.

The project imports symbols such as ``Ok``, ``Err``, ``Some``, ``NoneType``,
``PropagateError`` and ``propagate`` from the ``rust`` package. When the native
extension is not available, this module provides Python fallbacks so the
interpreter can still load the language runtime.
"""

from __future__ import annotations

try:
    from ._vyn_rust import (  # type: ignore[import-not-found]
        Ok,
        Err,
        Some,
        NoneType,
        PropagateError,
        propagate,
    )
except ImportError:
    class PropagateError(Exception):
        """Raised when a propagated error/result should stop evaluation."""

        def __init__(self, value=None):
            self.value = value
            super().__init__(repr(value))

    class _ResultBase:
        def is_ok(self) -> bool:
            return False

        def is_err(self) -> bool:
            return False

        def is_some(self) -> bool:
            return False

        def is_none(self) -> bool:
            return False

    class Ok(_ResultBase):
        def __init__(self, value):
            self._value = value

        def is_ok(self) -> bool:
            return True

        def unwrap(self):
            return self._value

        def expect(self, _msg=None):
            return self._value

        def unwrap_or(self, _default=None):
            return self._value

        def unwrap_or_else(self, _f=None):
            return self._value

        def map(self, f):
            return Ok(f(self._value))

        def and_then(self, f):
            return f(self._value)

        def or_else(self, _f):
            return self

        def __repr__(self):
            return f"Ok({self._value!r})"

    class Err(_ResultBase):
        def __init__(self, error):
            self._error = error

        def is_err(self) -> bool:
            return True

        def unwrap(self):
            raise RuntimeError(f"called `unwrap()` on an `Err` value: {self._error!r}")

        def expect(self, msg=None):
            raise RuntimeError(f"{msg}: {self._error!r}")

        def unwrap_or(self, default=None):
            return default

        def unwrap_or_else(self, f):
            return f(self._error)

        def map(self, _f):
            return self

        def and_then(self, _f):
            return self

        def or_else(self, f):
            return f(self._error)

        def error(self):
            return self._error

        def __repr__(self):
            return f"Err({self._error!r})"

    class Some(_ResultBase):
        def __init__(self, value):
            self._value = value

        def is_some(self) -> bool:
            return True

        def is_ok(self) -> bool:
            return True

        def unwrap(self):
            return self._value

        def expect(self, _msg=None):
            return self._value

        def unwrap_or(self, _default=None):
            return self._value

        def unwrap_or_else(self, _f=None):
            return self._value

        def map(self, f):
            return Some(f(self._value))

        def and_then(self, f):
            return f(self._value)

        def or_else(self, _f):
            return self

        def filter(self, predicate):
            if predicate(self._value):
                return Some(self._value)
            return NoneType()

        def __repr__(self):
            return f"Some({self._value!r})"

    class NoneType(_ResultBase):
        def __init__(self):
            pass

        def is_none(self) -> bool:
            return True

        def is_ok(self) -> bool:
            return False

        def is_err(self) -> bool:
            return False

        def unwrap(self):
            raise RuntimeError("called `unwrap()` on a `None` value")

        def expect(self, msg=None):
            raise RuntimeError(f"{msg}: None")

        def unwrap_or(self, default=None):
            return default

        def unwrap_or_else(self, f):
            return f()

        def map(self, _f):
            return self

        def and_then(self, _f):
            return self

        def or_else(self, f):
            return f()

        def filter(self, _predicate):
            return self

        def __repr__(self):
            return "None"

    def propagate(value):
        if isinstance(value, Ok):
            return value.unwrap()
        if isinstance(value, Some):
            return value.unwrap()
        if isinstance(value, Err):
            raise PropagateError(value)
        if isinstance(value, NoneType):
            raise PropagateError(value)
        return value


__all__ = ["Ok", "Err", "Some", "NoneType", "PropagateError", "propagate"]
