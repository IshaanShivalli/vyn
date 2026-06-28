from collections import ChainMap


def make_function_scope(params, args, outer_vars):
    """
    params: list of (name, default) tuples OR list of plain name strings
    args:   list of argument values
    """
    # FIX: handle both old-style (list of strings) and new-style (list of tuples)
    local = {}
    for i, param in enumerate(params):
        name = param[0] if isinstance(param, tuple) else param
        local[name] = args[i] if i < len(args) else None
    return ChainMap(local, outer_vars)


# LOCAL VARIABLES MODULE: Manages function-local scope using ChainMap
# Function parameters automatically create local variables:
# myFunc = function(x, y) perform  - x, y become local variables in function scope
#   result = x + y                 - local variables shadow global variables
#   return result
# endFunc