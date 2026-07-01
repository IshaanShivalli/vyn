import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from functions import functions as f


class ImportAndUnionTests(unittest.TestCase):
    def setUp(self):
        f.global_vars.variables.clear()

    def test_stdlib_module_import_exposes_module_namespace(self):
        f.execute_line("import math")
        self.assertIn("math", f.global_vars.variables)
        self.assertTrue(hasattr(f.global_vars.variables["math"], "sqrt"))
        self.assertAlmostEqual(f.eval_expression("math.sqrt(9)", f.global_vars.variables), 3.0)

    def test_union_definition_and_field_access(self):
        f._source.push([
            "union Number {",
            "  i: int",
            "  f: float",
            "}",
        ], stop_at_end=True)
        f.execute_line("union Number {")
        f._source.pop()

        f.execute_line("u = Number()")
        f.execute_line("u.i = 7")
        f.execute_line("u.f = 2.5")

        self.assertEqual(f.global_vars.variables["u"].get_attr("f"), 2.5)
        self.assertEqual(f.global_vars.variables["u"].get_attr("i"), 7)


if __name__ == "__main__":
    unittest.main()
