# structs/struct_methods.py
from collections import ChainMap

class StructMethod:
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
        def _bound(*args):
            return self._call(instance, *args)
        return _bound

    def _call(self, instance, *args):
        local_vars = {'this': instance}
        for i, param in enumerate(self.params):
            local_vars[param] = args[i] if i < len(args) else None

        scope = ChainMap(local_vars, self.outer_vars)
        result = None
        for line in self.body:
            res = self.run_body([line], scope)
            if isinstance(res, tuple) and res[0] == 'RETURN':
                result = res[1]
                break
        return result