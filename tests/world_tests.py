import unittest
from math import pi, sin, cos, tan, atan, hypot, sqrt
from pc.models.world import World, WorldUpdater
from pc.models.models import *
from pc.models.vision import *
from numpy.testing import assert_almost_equal
from postprocessing import Postprocessing
from Polygon.cPolygon import Polygon

class TestWorld(unittest.TestCase):
	"""
	Tests the creation and initialisation of the world
	"""
	def setUp(self):
		pass

	def test_wrong_initialisation(self):
		"""
		This test checks if the World object can be initialised incorrectly
		"""
		self.assertRaises(ValueError, World, "left", None)
		self.assertRaises(ValueError, World, None, 0)
		self.assertRaises(ValueError, World, None, None)


	def test_wrong_assignment(self):
		"""
		This test checks if the World object can be assigned a wrong value
		"""
		world = World("left", 0)
		self.assertRaises(ValueError, setattr, world, 'our_attacker', None)
		self.assertRaises(ValueError, setattr, world, 'their_attacker', None)
		self.assertRaises(ValueError, setattr, world, 'our_defender', None)
		self.assertRaises(ValueError, setattr, world, 'their_defender', None)
		self.assertRaises(ValueError, setattr, world, 'ball', None)
		self.assertRaises(ValueError, setattr, world, 'our_goal', None)
		self.assertRaises(ValueError, setattr, world, 'their_goal', None)
		self.assertRaises(ValueError, setattr, world, 'pitch', None)

class TestWorldUpdater(unittest.TestCase):
	"""
	Test the creation and functions inside of WorldUpdater
	"""
	def setUp(self):
		pass

	def test_wrong_initialization(self):
		"""
		Wrong initialisation test
		"""
		self.assertRaises(ValueError, WorldUpdater, None)
		self.assertRaises(ValueError, WorldUpdater, 0, None, None, None, None)

	def test_cm_to_px(self):
		world = World("right",0)
		worldupdater = WorldUpdater(0,"yellow","left",)
		self.assert_almost_equal(worldupdater.cm_to_px(15), 2.36979166667*15) 

if __name__ == '__main__':
	unittest.main()


