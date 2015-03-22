import unittest
from tests import models_tests, postprocessing_tests.py, planner_tests, world_tests
'''
This just aggregates and runs all of the tests from the tests folder
'''

if __name__ == "__main__":
suite = unittest.TestLoader().loadTestsFromModule(models_tests)
suite.addTests(unittest.TestLoader().loadTestsFromModule(postprocessing_tests.py))
suite.addTests(unittest.TestLoader().loadTestsFromModule(planner_tests))
suite.addTests(unittest.TestLoader().loadTestsFromModule(world_tests))
unittest.TextTestRunner(verbosity=2).run(suite)