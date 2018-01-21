# 
# This operator interpolates a series of sample points using hermite interpolation.
# 
# It hybrids Vector(V-V) and Aligned(V-L) bezier control types in one Curve.Spline. 
# But only one handle type is allowed at ONE control point.
# 
# Reference: 
# https://stackoverflow.com/questions/1030596/drawing-hermite-curves-in-opengl
# https://docs.blender.org/api/blender_python_api_2_57_1/bpy.types.BezierSplinePoint.html#bpy.types.BezierSplinePoint.handle_left_type
# https://pythonapi.upbge.org/bpy.types.BezierSplinePoint.html
# 
# Challenge: Use Blender's Bezier Curve as basis to straighten curves between two control points if specified (Try using the Vector and Aligned Handle Type of Blender's Bezier Points)
# 

import bpy

# I/O Parser
# Input: CSV file with only x-y-z coordinate of control points
# Output: Bezier spline with control points at specified x-y-z coordinates
# Algorithm: Assign either V-V or V-L handler type to control points based on WAHT?


# CUrve Parser
# Input: A Curve Object in Blender Context Scene
# Output: A Hermite Inpterpolated Spline through the given control points
# Challenge: Straighten between control points


# Core Algorithm
# Input: List of Bezier points in a spline / or in a CURVE?
# Output: bpy.data.curve -> bpy.data.mesh


# Core Algorithm
# 
# 

# Get Current Scene's Active Object
def get_active_object():
	return bpy.context.active_object

# Main Function
def main():
	print('in main')

	# get current active object in scene
	obj = get_active_object()
	print(obj)


if __name__ == '__main__':
	main()