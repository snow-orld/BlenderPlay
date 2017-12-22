# This script uses bmesh to make cubic hermite spline interpolation of multiple given points.

import bpy
import bmesh
from mathutils import Vector

def get_vertex_list():
	
	v1 = (0,1,0)
	v2 = (1,1,0)
	v3 = (1,0,0)
	v4 = (0,0,0)

	return [v1, v2, v3, v4]

def catmull_rom(spline, index, p0, m0, p1, m1, res=8):
	# REF: "Interpolating a data set" on wiki page "Cubic Hermite spline"
	# Translate to Bezier Curve p0, p0 + m0/3, p1 - m1/3, p1
	prev_index = (index - 1) % len(spline.bezier_points)
	succ_index = (index + 1) % len(spline.bezier_points)
	succ_succ_index = (index + 2) % len(spline.bezier_points)

	spline.bezier_points[index].co = p0
	spline.bezier_points[index].handle_right = m0
	spline.bezier_points[index].handle_left = Vector(p1) - Vector(m0)
	spline.bezier_points[succ_index].co = p1
	spline.bezier_points[succ_index].handle_left = m1
	spline.bezier_points[succ_index].handle_right = Vector(p0) - Vector(m1)

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

def main():
	
	vertex_list = get_vertex_list()

	cubic_hermite(vertex_list)

if __name__ == '__main__':
	main()