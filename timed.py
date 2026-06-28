# timed.py - Timed block implementation
# Measures execution time of a block of code

import time

# Stores all timed block results: label -> seconds
_timed_results = {}


def start_timer():
    """Returns the current time in nanoseconds."""
    return time.perf_counter_ns()


def stop_timer(start_ns):
    """
    Returns elapsed time as a readable string.
    Automatically picks the best unit.
    """
    elapsed_ns = time.perf_counter_ns() - start_ns

    if elapsed_ns < 1_000:
        return f"{elapsed_ns}ns"
    elif elapsed_ns < 1_000_000:
        return f"{elapsed_ns / 1_000:.3f}µs"
    elif elapsed_ns < 1_000_000_000:
        return f"{elapsed_ns / 1_000_000:.3f}ms"
    else:
        return f"{elapsed_ns / 1_000_000_000:.3f}s"


def store_result(label, elapsed_str):
    """Store timed result under a label."""
    _timed_results[label] = elapsed_str


def get_result(label):
    """Get a stored timed result."""
    return _timed_results.get(label, None)


def list_results():
    """Return all stored timed results."""
    return dict(_timed_results)


def clear_results():
    """Clear all stored results."""
    _timed_results.clear()