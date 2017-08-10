import bpy
from mathutils import Vector

w = 1 # weight
cList = [Vector((0,0,0)),Vector((1,0,0)),Vector((2,0,0)),Vector((2,3,0)),
        Vector((0,2,1))]

def MakePolyLine(objname, curvename, cList):

	curvedata = bpy.data.curves.new(name=curvename, type='CURVE')
	curvedata.dimensions = '3D'

	objectdata = bpy.data.objects.new(objname, curvedata)
	objectdata.location = (0,0,0) #object origin
	bpy.context.scene.objects.link(objectdata)

	polyline = curvedata.splines.new('POLY')
	polyline.points.add(len(cList)-1)
	for num in range(len(cList)):
		x, y, z = cList[num]
		polyline.points[num].co = (x, y, z, w)

MakePolyLine("Track", "Central Line", cList)