
# blender 2.6x  , printing world coordinates
import bpy  
import random

current_obj = bpy.context.active_object  

print("="*40) # printing marker  
cnt = 0
for face in current_obj.data.polygons:  
	if (cnt > 0):
		break
	verts_in_face = face.vertices[:]
	print("face index", face.index) 
	print("normal", face.normal)
	for vert in verts_in_face:
		local_point = current_obj.data.vertices[vert].co
		world_point = current_obj.matrix_world * local_point
		print("vert", vert, " vert co", world_point)

	cnt += 1

# for uv in current_obj.data.uv_layers[0].data:
# 	print(uv.uv)

import bmesh
from mathutils import Vector

obj = bpy.context.edit_object
me = obj.data
bm = bmesh.from_edit_mesh(me)


def uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return uv_data.uv
    return None


def uv_from_vert_average(uv_layer, v):
    uv_average = Vector((0.0, 0.0))
    total = 0.0
    for loop in v.link_loops:
        uv_average += loop[uv_layer].uv
        total += 1.0

    if total != 0.0:
        return uv_average * (1.0 / total)
    else:
        return None

# Example using the functions above
uv_layer = bm.loops.layers.uv.active

for v in bm.verts:
    uv_first = uv_from_vert_first(uv_layer, v)
    uv_average = uv_from_vert_average(uv_layer, v)
    print("Vertex: %r, uv_first=%r, uv_average=%r" % (v, uv_first, uv_average))


# Draw tangent at each vertex
data = bpy.data.curves.new(name='tangent', type='CURVE')
data.dimensions = '3D'
helperobj = bpy.data.objects.new('tangent', data)
helperobj.location = obj.location
bpy.context.scene.objects.link(helperobj)

for face in me.polygons:
	# loop over face loop
	for vert in [me.loops[i] for i in face.loop_indices]:
		tangent = vert.tangent
		normal = vert.normal
		bitangent = vert.bitangent_sign * normal.cross(tangent)
		index = vert.vertex_index
		co = me.vertices[index].co

		poly = data.splines.new('POLY');
		poly.points.add(1)
		poly.points[0].co = (co.x, co.y, co.z, 1)
		poly.points[1].co = (co.x + 5*tangent.x, co.y + 5*tangent.y, co.z + 5*tangent.z, 1)

	
