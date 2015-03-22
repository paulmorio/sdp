import unittest
from math import pi, sin, cos, tan, atan, hypot, sqrt
from pc.models.models import *
from numpy.testing import assert_almost_equal
from Polygon.cPolygon import Polygon

class TestCoordinate(unittest.TestCase):
	'''
	Tests the Coordinate class.
	'''
	def setUp(self):
		pass
	def test_wrong_initialisation(self):
		'''
		This test checks if the Coordinate object can be initialised incorrectly
		'''
		self.assertRaises(ValueError, Coordinate, None, 5)
		self.assertRaises(ValueError, Coordinate, 5, None)
		self.assertRaises(ValueError, Coordinate, None, None)
	def test_wrong_assignment(self):
		'''
		This test checks if the Coordinate object can be assigned a wrong value
		'''
		coord = Coordinate(10, 10)
		self.assertRaises(ValueError, setattr, coord, 'x', None)
		self.assertRaises(ValueError, setattr, coord, 'y', None)