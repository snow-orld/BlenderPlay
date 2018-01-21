# This script uses bmesh to make cubic hermite spline interpolation of multiple given points.

import bpy
import bmesh
from mathutils import Vector
from numpy import *

RES = 8

def get_vertex_list():
	
	v1 = (0,10,0)
	v2 = (1,10,0)
	v3 = (10,0,0)
	v4 = (0,0,0)

	return [v1, v2, v3, v4]

def bezier(p0, p1, p2, p3, resolution):

	points = []

	for t in linspace(0, 1, resolution + 1):
		point = (1-t)*(1-t)*(1-t)*p0 + 3*(1-t)*(1-t)*t*p1 + 3*(1-t)*t*t*p2 + t*t*t*p3
		points.append(point)

	return points

def catmull_rom(spline, index, p0, m0, p1, m1, res=8):
	# REF: "Interpolating a data set" on wiki page "Cubic Hermite spline"
	# Translate to Bezier Curve p0, p0 + m0/3, p1 - m1/3, p1
	prev_index = (index - 1) % len(spline.bezier_points)
	succ_index = (index + 1) % len(spline.bezier_points)
	succ_succ_index = (index + 2) % len(spline.bezier_points)

	spline.bezier_points[index].co = p0
	spline.bezier_points[index].handle_right = Vector(p0) + Vector(m0) *0.33
	spline.bezier_points[index].handle_left = Vector(p1) - Vector(m0)*0.33
	spline.bezier_points[index].handle_right_type = 'ALIGNED'
	spline.bezier_points[index].handle_left_type = 'ALIGNED'
	spline.bezier_points[succ_index].co = p1
	spline.bezier_points[succ_index].handle_left = Vector(p1) - Vector(m1)*0.33
	spline.bezier_points[succ_index].handle_right = Vector(p0) - Vector(m1)*0.33
	spline.bezier_points[succ_index].handle_left_type = 'ALIGNED'
	spline.bezier_points[succ_index].handle_right_type = 'ALIGNED'
	
def cubic_hermite(vlist):
	# REF: https://blender.stackexchange.com/questions/12201/bezier-spline-with-python-adds-unwanted-pointß
	
	curvedata = bpy.data.curves.new(name='Curve', type='CURVE')
	curvedata.dimensions = '3D'
	
	objectdata = bpy.data.objects.new('Curve', curvedata)
	objectdata.location = (0,0,0) #object origin
	bpy.context.scene.objects.link(objectdata)

	spline = curvedata.splines.new('BEZIER')
	spline.bezier_points.add(len(vlist)-1)

	for index, v in enumerate(vlist):

		prev_index = (index - 1) % len(vlist)
		succ_index = (index + 1) % len(vlist)
		succ_succ_index = (index + 2) % len(vlist)

		p0 = v
		p1 = vlist[succ_index]
		m0 = Vector(p1) - Vector(vlist[prev_index])
		m1 = Vector(vlist[succ_succ_index]) - Vector(p0)

		catmull_rom(spline, index, p0, m0, p1, m1)

def cubicHermite(vlist):

	curvedata = bpy.data.curves.new(name='Curve', type='CURVE')
	curvedata.dimensions = '3D'

	objectdata = bpy.data.objects.new('Curve', curvedata)
	objectdata.location = (0,0,0)
	bpy.context.scene.objects.link(objectdata)

	for index, v in enumerate(vlist):

		prev_index = (index - 1) % len(vlist)
		succ_index = (index + 1) % len(vlist)
		succ_succ_index = (index + 2) % len(vlist)

		p_prev = Vector(vlist[prev_index])
		p_cur = Vector(v)
		p_next = Vector(vlist[succ_index])
		p_next_next = Vector(vlist[succ_succ_index])

		m_cur = Vector(p_next) - Vector(p_prev)
		m_next = Vector(p_next_next) - Vector(p_cur)	

		polyline = curvedata.splines.new('POLY')
		polyline.points.add(RES)

		# Sample with cubic hermite spline for each interval
		for i in range(RES):
			t = i / RES
			x, y, z = p_cur*(2*t*t*t-3*t*t)+m_cur*(p_next[0]-p_cur[0])*(t*t*t-2*t*t+t)+p_next*(-2*t*t*t+3*t*t)+m_next*(p_next[0]-p_cur[0])*(t*t*t-3*t*t)
			polyline.points[i].co = (x,y,z,1)

def main():
	
	vertex_list = get_vertex_list()

	# cubic_hermite(vertex_list)
	# cubicHermite(vertex_list)

if __name__ == '__main__':
	main()