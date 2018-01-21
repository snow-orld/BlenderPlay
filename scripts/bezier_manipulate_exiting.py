#
# Explointing the bezier curve's control points
#
# REF: https://blenderscripting.blogspot.jp/2016/05/the-coordinates-of-curve-control-points.html
# API: https://docs.blender.org/api/blender_python_api_2_57_1/bpy.types.BezierSplinePoint.html#bpy.types.BezierSplinePoint.handle_left_type
#

import bpy
from mathutils import Vector
import math
from numpy import *

obj = bpy.context.active_object

if obj.type == 'CURVE':

	for subcurve in obj.data.splines:

		mat = obj.matrix_world

		curvetype = subcurve.type
		print('curve type:', curvetype)

		if curvetype == 'BEZIER':
			print("curve is closed:", subcurve.use_cyclic_u)

			# print(dir(subcurve))
			for bezpoint in subcurve.bezier_points:
				"""
				'co',					 # Coordinates of the control point, float array of 3 items in [-inf, inf], default (0.0, 0.0, 0.0)
				'handle_left',			 # Coordinates of the first handle
				'handle_left_type',      # Handle types, enum in [‘FREE’, ‘AUTO’, ‘VECTOR’, ‘ALIGNED’], default ‘FREE’
				'handle_right',			 # Coordinates of the second handle
				'handle_right_type',     # Handle types
				'hide',                  # is it hidden?
				'radius',                # Radius for bevelling, float in [0, inf], default 0.0
				'select_control_point',  # is it selected?, boolean, default False
				'select_left_handle',    #
				'select_right_handle',   #
				'tilt'                   # Tilt in 3D View, float in [-inf, inf], default 0.0
				'weight_softbody',		 # Softbody goal weight, float in [-inf, inf], default 0.0
				# use     print(dir(bezpoint))  to see all
				"""
				# print('\n')
				# print('co', mat * bezpoint.co)
				# print('handle_left', mat * bezpoint.handle_left)
				# print('handle_left_type', bezpoint.handle_left_type)
				# print('handle_right', mat * bezpoint.handle_right)
				# print('handle_right_type', bezpoint.handle_right_type)
				# print('radius', bezpoint.radius)
				# print('tilt', bezpoint.tilt)

def planViewBezier(obj):

	print('\nGenerating Bezier Spline in Plan View...')

	if obj.type == 'CURVE':

		datacpy = obj.data.copy()
		datacpy.name = obj.data.name + 'planView'

		objcpy = bpy.data.objects.new(obj.name + '_planView', datacpy)
		
		objcpy.location = (obj.location.x + 1, obj.location.y + 1, 0)

		bpy.context.scene.objects.link(objcpy)

		for subcurve in datacpy.splines:

			if subcurve.type == 'BEZIER':

				for bezpoint in subcurve.bezier_points:
					
					bezpoint.co.x = round(bezpoint.co.x, 2)
					bezpoint.co.y = round(bezpoint.co.y, 2)
					bezpoint.co.z = 0

					bezpoint.handle_left.x = round(bezpoint.handle_left.x, 2)
					bezpoint.handle_left.y = round(bezpoint.handle_left.y, 2)
					bezpoint.handle_left.z = 0

					bezpoint.handle_right.x = round(bezpoint.handle_right.x, 2)
					bezpoint.handle_right.y = round(bezpoint.handle_right.y, 2)
					bezpoint.handle_right.z = 0

					bezpoint.tilt = round(bezpoint.tilt) % 360

					print("\n")
					print('co', bezpoint.co)
					print('left_handle', bezpoint.handle_left)
					print('right_handle', bezpoint.handle_right)
					print('tilt', bezpoint.tilt)

def getSamplePoints(spline, resolution):
	
	print(resolution)

	points = []

	for index in range(len(spline.bezier_points) - 1):

		ctrlPnt = spline.bezier_points[index]
		nextPnt = spline.bezier_points[index + 1]

		points += bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, resolution)

	if spline.use_cyclic_u:

		ctrlPnt = spline.bezier_points[len(spline.bezier_points) - 1]
		nextPnt = spline.bezier_points[0]

		points += bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, resolution)

	return points

def bezier(p0, p1, p2, p3, resolution):

	points = []

	for t in linspace(0, 1, resolution + 1):
		point = (1-t)*(1-t)*(1-t)*p0 + 3*(1-t)*(1-t)*t*p1 + 3*(1-t)*t*t*p2 + t*t*t*p3
		points.append(point)

	return points

def addPoly2Object(curvedata, points):

	polyline = curvedata.splines.new('POLY')
	polyline.points.add(len(points) - 1)

	for i in range(len(points)):
		x, y, z = points[i]
		polyline.points[i].co = (x, y, z, 1)

def addCurveObject(objname):

	curvedata = bpy.data.curves.new(name=objname, type='CURVE')
	curvedata.dimensions = '3D'

	obj = bpy.data.objects.new(objname, curvedata)
	obj.location = (0,0,0)
	bpy.context.scene.objects.link(obj)

	return obj

def sampleBezier(obj):

	if (obj.type == 'CURVE'):

		newobj = addCurveObject(obj.name + '_sampled')
		newobj.scale = obj.scale

		for subcurve in obj.data.splines:

			if subcurve.type == 'BEZIER':
				print('\nsubcurve', subcurve)
				points = getSamplePoints(subcurve, 12)
				addPoly2Object(newobj.data, points)

