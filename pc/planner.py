"""
This script updates the worldstate of the pitch by calling the vision module to
update the worldstate instance's variables, and then creates appropiate plans 
for the robot.
"""
import robot
import worldmodel

# Choose between one of the two.
import camera
import vision

class Planner():
	
	def __init__(self, worldState, inputFrame):
		self.worldState = worldState
		self.frame = inputFrame

	def updateWorldState():
		"""
		Updates the worldstate from video frame information.

		:return: None
		"""
		pass

	def goToBall():
		"""
		Simple function to have robot go to ball (regardless of competition
		constraints)

		:return: None
		"""



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    
