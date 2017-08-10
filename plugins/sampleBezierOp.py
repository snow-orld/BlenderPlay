bl_info = {
	"name": "Sample Bezier",
	"category": "Object",
}

import bpy
from numpy import *

class ObjectSampleBezierCurve(bpy.types.Operator):
	"""Object Cursor Array"""
	bl_idname = "object.sample_bezier"
	bl_label = "Sample Bezier"
	bl_options = {'REGISTER', 'UNDO'}

	resolution = bpy.props.IntProperty(name="Resolution", default=2, min=1, max=100)

	def bezier(self, p0, p1, p2, p3, resolution):
		points = []
		for t in linspace(0, 1, resolution + 1):
			point = (1-t)*(1-t)*(1-t)*p0 + 3*(1-t)*(1-t)*t*p1 + 3*(1-t)*t*t*p2 + t*t*t*p3
			points.append(point)

		return points

	def getSamplePoints(self, spline):
		points = []

		for index in range(len(spline.bezier_points) - 1):

			ctrlPnt = spline.bezier_points[index]
			nextPnt = spline.bezier_points[index + 1]

			points += self.bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, self.resolution)

		if spline.use_cyclic_u:

			ctrlPnt = spline.bezier_points[len(spline.bezier_points) - 1]
			nextPnt = spline.bezier_points[0]

			points += self.bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, self.resolution)

		return points

	def cleanSplines(self, obj):
		
		if (obj.type != 'CURVE'):
			return

		if (len(obj.data.splines)):
			for spline in obj.data.splines:
				obj.data.splines.remove(spline)

	def addSpline(self, obj, points):

		if (obj.type != 'CURVE'):
			return

		polyline = obj.data.splines.new('POLY')
		polyline.points.add(len(points) - 1)

		for i in range(len(points)):
			x, y, z = points[i]
			polyline.points[i].co = (x, y, z, 1)

	def sampleBezierCurveObject(self, obj):

		if (obj.type != 'CURVE'):
			return

		if (bpy.data.objects.find(obj.name + '_sampled') == -1):

			curve = bpy.data.curves.new(name=obj.name + '_sampled', type='CURVE')
			curve.dimensions = '3D'

			newobj = bpy.data.objects.new(obj.name + '_sampled', curve)
			newobj.location = (obj.location.x + 1, obj.location.y + 1, obj.location.z)
			bpy.context.scene.objects.link(newobj)

		sampledobj = bpy.data.objects[obj.name + '_sampled']
		sampledobj.select = True
		obj.select = False

		self.cleanSplines(sampledobj)

		for spline in obj.data.splines:
			points = self.getSamplePoints(spline)
			self.addSpline(sampledobj, points)

	def execute(self, context):
		scene = context.scene
		obj = scene.objects.active

		self.sampleBezierCurveObject(obj)
		
		return {'FINISHED'}


def menu_func(self, context):
	self.layout.operator(ObjectSampleBezierCurve.bl_idname)

def register():
	bpy.utils.register_class(ObjectSampleBezierCurve)
	bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
	bpy.utils.unregister_class(ObjectSampleBezierCurve)
	bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
	register()