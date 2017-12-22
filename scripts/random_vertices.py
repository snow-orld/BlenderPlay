# This script uses bmesh to generate random multiple points within given range.

import bpy
import bmesh
import random

POINTS_NUM = 5
X_RANGE = 10
Y_RANGE = 10
Z_RANGE = 0

def generate_random_knots(bm, pnum, length, width, height):
	# generate pnum random vertices as control points to be interpolated by the cubic hermite spline
	knots = []
	
	for i in range(pnum):
		# NOTICE: -0.5 is not an optimal way to get the random number around 0. Recently watched video on bilibili explains why. But WHICH video?
		x = round((random.random() - 0.5) * length, 2)
		y = round((random.random() - 0.5) * width, 2)
		z = round((random.random() - 0.5) * height, 2)

		knots.append((x, y, z))
		bm.verts.new((x, y, z))

	return knots

def main():
	# Make a new BMesh
	bm = bmesh.new()
	vertices = generate_random_knots(bm, POINTS_NUM, X_RANGE, Y_RANGE, Z_RANGE)

	me = bpy.data.meshes.new("object")
	obj = bpy.data.objects.new('object', me)
	bpy.context.scene.objects.link(obj)

	bpy.context.scene.objects.active = obj
	obj.select = True

	bm.to_mesh(me)
	bm.free()

if __name__ == '__main__':
	main()