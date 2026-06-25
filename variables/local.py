from collections import ChainMap


def make_function_scope(params, args, outer_vars):
    local = {name: val for name, val in zip(params, args)}
    return ChainMap(local, outer_vars)


# LOCAL VARIABLES MODULE: Manages function-local scope using ChainMap
# Function parameters automatically create local variables:
# myFunc = function(x, y) perform  - x, y become local variables in function scope
#   result = x + y                 - local variables shadow global variables
#   return result
# endFunc
