import bpy
import bmesh
from mathutils import Vector

bm = bmesh.new()

v1 = bm.verts.new((0, 0, 0))
v2 = bm.verts.new((0, 1, 0))
v3 = bm.verts.new((2, 0, 0))
v4 = bm.verts.new((2, 1, 0))

bm.edges.new([v1, v2])
bm.edges.new([v3, v4])

me = bpy.data.meshes.new('object')
obj = bpy.data.objects.new('object', me)
bpy.context.scene.objects.link(obj)

bpy.context.scene.objects.active = obj
obj.select = True

bm.to_mesh(me)
bm.free()