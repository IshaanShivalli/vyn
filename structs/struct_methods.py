# structs/struct_methods.py
from types import MethodType

class StructMethod:
    """Wrapper for struct methods"""
    def __init__(self, name, params, body, outer_vars, eval_expression, run_body):
        self.name = name
        self.params = params
        self.body = body
        self.outer_vars = outer_vars
        self.eval_expression = eval_expression
        self.run_body = run_body

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return MethodType(self._bound_method, instance)

    def _bound_method(self, instance, *args):
        # Create local scope with 'this' pointing to the instance
        local_vars = {'this': instance}
        
        # Bind parameters
        for i, param in enumerate(self.params):
            if i < len(args):
                local_vars[param] = args[i]
            else:
                local_vars[param] = None

        # Execute method body
        from collections import ChainMap
        scope = ChainMap(local_vars, self.outer_vars)

        result = None
        for line in self.body:
            res = self.run_body([line], scope)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                result = res[1]
                break

        return result