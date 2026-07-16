import contextlib
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from functions import functions as f


class RuntimeLibraryPathTests(unittest.TestCase):
    def setUp(self):
        f.global_vars.variables.clear()

    def test_dof_finds_examples_by_filename(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            f.execute_line('DOF("13_database.vyn")', f.global_vars.variables)
        self.assertIn("Ada", output.getvalue())
        self.assertIn("Grace", output.getvalue())

    def test_random_import_uses_vyn_lib_wrapper(self):
        f.execute_line("import random", f.global_vars.variables)
        self.assertIn("randint", f.global_vars.variables)
        self.assertIn("vyn-lib", f.global_vars.variables["random"].__file__)
        self.assertIs(f.global_vars.variables["Random"], f.global_vars.variables["random"])

    def test_choice_accepts_multiple_values(self):
        f.execute_line("import random", f.global_vars.variables)
        result = f.eval_expression("choice(1, 2, 5, 6)", f.global_vars.variables)
        self.assertIn(result, (1, 2, 5, 6))

    def test_attribute_call_errors_do_not_escape_repl(self):
        f.execute_line("import random", f.global_vars.variables)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            f.execute_line("random.choice(1)", f.global_vars.variables)
        self.assertIn("Error in function call", output.getvalue())


if __name__ == "__main__":
    unittest.main()
