# trait registry: (trait_name, type_name) -> dict of method_name -> (params, body, outer_vars, eval_expression, run_body)
_impls = {}
# type_name -> list of trait names
_type_traits = {}

def register_impl(trait_name, type_name, methods):
    """methods: dict method_name -> (params, body, outer_vars, eval_expression, run_body)"""
    key = (trait_name, type_name)
    _impls[key] = methods
    _type_traits.setdefault(type_name, []).append(trait_name)

def get_trait_methods_for_type(type_name):
    """Return a dict of all methods from all traits implemented for this type."""
    result = {}
    for trait in _type_traits.get(type_name, []):
        key = (trait, type_name)
        methods = _impls.get(key, {})
        for mname, (params, body, outer_vars, eval_expr, run_body) in methods.items():
            result[mname] = (params, body, outer_vars, eval_expr, run_body)
    return result