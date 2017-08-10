bl_info = {
	"name": "Test Addon",
	"category": "Object",
}

import bpy
from bpy_extras.io_utils import unpack_list

class ObjectTestAddon(bpy.types.Operator):
	"""Test Addon Script"""				# blender will use this as a tooltip for menu items and buttons.
	bl_idname = "object.test_addon"		# unique identifier for buttons and menu items to reference.
	bl_label = "Test Addon"				# display name in the interface.
	bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.

	filename = "D:\Documents\Blender\data\Central.csv"
	objname = "Central Curve"
	vList = {'Total': []}

	crosssection_obj = None
	# curves = {}

	def makeCrossSection(self):

		curvedata = bpy.data.curves.new(name='Crosssection', type='CURVE')
		curvedata.dimensions = '3D'

		self.crosssection_obj = bpy.data.objects.new('Crosssection', curvedata)
		self.crosssection_obj.location = (0, -20, 0)
		bpy.context.scene.objects.link(self.crosssection_obj)

		polyline = curvedata.splines.new('POLY')
		polyline.points.add(1)

		ends = [(-5.5,0,0), (5.5,0,0)]
		w = 1
		for i in range(len(ends)):
			x, y, z = ends[i]
			polyline.points[i].co = (x, y, z, w)

	def read(self):
		
		with open(self.filename, "r") as f:
			trackname = ""
			for line in f:
				if (line[0] == 'T'):
					trackname = line.split('\n')[0]
					# print(trackname)
					self.vList[trackname] = []
				else:
					x, y, z = [float(s) for s in line.split(',')]
					self.vList[trackname].append((x, y, z))
					self.vList['Total'].append((x, y, z))
					# print(trackname, x, y, z)

	def makePolyLine(self, curvename, datalist):

		curvedata = bpy.data.curves.new(name=curvename, type='CURVE')
		curvedata.dimensions = '3D'

		objectdata = bpy.data.objects.new(curvename, curvedata)
		objectdata.location = (0,0,0) 	#object origin
		bpy.context.scene.objects.link(objectdata)

		polyline = curvedata.splines.new('POLY')
		polyline.points.add(len(datalist) - 1)

		w = 1
		for i in range(len(datalist)):
			x, y, z = datalist[i]
			polyline.points[i].co = (x, y, z, w)

		curvedata.bevel_object = self.crosssection_obj
		curvedata.twist_mode = "Z_UP"
		# self.curves[curvename] = objectdata

	def makeSpline(self):

		for key in self.vList:
			self.makePolyLine(key, self.vList[key])


	def execute(self, context):			# execute() is called by blender when running the operator.

		# The original script
		scene = context.scene
		self.read()
		self.makeCrossSection()
		self.makeSpline()

		return {'FINISHED'}            # this lets blender know the operator finished successfully.


def register():
	bpy.utils.register_class(ObjectTestAddon)


def unregister():
	bpy.utils.unregister_class(ObjectTestAddon)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
	register()