import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from functions import functions as f


class StructIntegrationTests(unittest.TestCase):
    def setUp(self):
        f.global_vars.variables.clear()

    def test_struct_definition_and_field_access(self):
        f._source.push([
            "struct Point {",
            "  x: int",
            "  y: float",
            "}",
        ], stop_at_end=True)
        f.execute_line("struct Point {")
        f._source.pop()

        f.execute_line("p = Point()")
        f.execute_line("p.x = 5")
        f.execute_line("p.y = 2.5")

        self.assertEqual(f.global_vars.variables["p"].get_attr("x"), 5)
        self.assertEqual(f.global_vars.variables["p"].get_attr("y"), 2.5)


if __name__ == "__main__":
    unittest.main()
