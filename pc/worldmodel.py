"""
Module Describes the state of the world which the football robots reside in.

A world state can be maintained and updated via instantiation of the Worldmodel.
All of the other classes inside of this module model entities that are attributes
of the world state.
"""

class Ball():

	def __init__(self, x_pos, y_pos):
		"""

		:param: x_pos: describes the x coordinate position of the ball
		:param: y_pos: describes the y coordinate position of the ball
		:return:
		"""

		self.x_pos = x_pos
		self.y_pos = y_pos

class DefensiveField():
	"""
	This class defines a defensive field as 6 (int, int) coordinates.
	"""

	def __init__(self):


	def __init__(self, cord1, cord2, cord3, cord4, cord5, cord6):
		"""

		:param cord1: The (x,y) coordinate tuple of the first point to define 
		the perimeter of the shape. This is the most important point.
		:param cord2: The (x,y) coordinate tuple of the second point to define
		 the perimeter of the shape
		:param cord3: The (x,y) coordinate tuple of the third point to define
		 the perimeter of the shape
		:param cord4: The (x,y) coordinate tuple of the fourth point to define
		 the perimeter of the shape
 		:param cord5: The (x,y) coordinate tuple of the fifth point to define
 		 the perimeter of the shape
		:param cord6: The (x,y) coordinate tuple of the sixth point to define
		 the perimeter of the shape
		:return:
		"""

		# Need to discuss this as essentially we can work with one tuple binding and
		# define all the other points through arithmetic transformation of the first point
		# using constants

		self.cord1 = cord1
		self.cord2 = cord2
		self.cord3 = cord3
		self.cord4 = cord4
		self.cord5 = cord5
		self.cord6 = cord6

class OffensiveField():
	"""
	This class defines an offensive area of the field through 4 cordinate tuples (x,y)
	"""

	def __init__(self):
		"""
		Creates a field with (0,0) cordinates
		"""
		self.cord1 = (0,0)
		self.cord2 = (0,0)
		self.cord3 = (0,0)
		self.cord4 = (0,0)

	def __init__(self, cord1, cord2, cord3, cord4):
		"""
		Standard way to initialize an offensive field, with the provided points

		:param cord1: The (x,y) coordinate tuple of the first point to define 
		the perimeter of the shape. This is the most important point.
		:param cord2: The (x,y) coordinate tuple of the first point to define 
		the perimeter of the shape.
		:param cord3: The (x,y) coordinate tuple of the first point to define 
		the perimeter of the shape.
		:param cord4: The (x,y) coordinate tuple of the first point to define 
		the perimeter of the shape.
		:return: 
		"""

		self.cord1 = cord1
		self.cord2 = cord2
		self.cord3 = cord3
		self.cord4 = cord4

class Robot():
	"""
	This class is different from the robot class defined in the robot module
	Objects of this class at this stage only contain information of a robot's 
	position and orientation described by a (x,y) coordinate and vector 
	respectively
	"""

	






class Worldmodel():

    