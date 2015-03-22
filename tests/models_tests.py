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

class TestVector(unittest.TestCase):
	'''
	Tests the Vector class.
	Our assumption is that Vector extends Coordinate so we do not retest
	the coordinate attribute initialisation and assignment.
	'''
	def setUp(self):
		pass

	def test_wrong_initialisation(self):
		'''
		This test checks if the Vector object can be initialised incorrectly.
		'''
		#Incorrect angle:
		self.assertRaises(ValueError, Vector, 2, 5, -0.5, 2)
		self.assertRaises(ValueError, Vector, 2, 5, 7, 2)
		self.assertRaises(ValueError, Vector, 2, 5, 2*pi, 3)

	def test_wrong_assignment(self):
		'''
		This test checks if the Vector object can be incorrectly updated.
		'''
		vec = Vector(2, 5, pi, 10)
		#Incorrect angle:
		self.assertRaises(ValueError, setattr, vec, 'angle', -0.5)
		self.assertRaises(ValueError, setattr, vec, 'angle', 10)
		#Incorrect velocity:
		self.assertRaises(ValueError, setattr, vec, 'velocity', -1)
	
	def test_correct_assignment(self):
		'''
		This test checks if the edge values of speed and angle can be chosen.
		There is no way of checking if something does not raise an error, so
		I'm just using a hack...
		'''
		try:
			vec = Vector(2, 5, 0, 5)
			vec.angle = 0
			vec = Vector(2, 5, 2*pi-0.1, 0)
			vec.speed = 0
		except ValueError:
			#This should raise no errors!
			self.assertTrue(False)