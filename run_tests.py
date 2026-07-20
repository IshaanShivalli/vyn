import pytest
import sys

# Add the PL directory to the Python path to ensure that all modules can be found
sys.path.append(r"c:\Users\Admin\Documents\lua\PL")

# Run the tests
pytest.main([r"c:\Users\Admin\Documents\lua\PL\tests"])