import bpy
import bmesh

"""
bmesh design doc: 
https://wiki.blender.org/index.php/Dev:Source/Modeling/BMesh/Design
latest api (BMesh Module):
https://docs.blender.org/api/blender_python_api_current/bmesh.html
https://docs.blender.org/api/blender_python_api_current/bmesh.types.html#base-mesh-type
"""

"""
challeges:
1.	Looping through bmesh's verts, edges, faces encounter "outdated index"
	Sol. https://blender.stackexchange.com/questions/31738/how-to-fix-outdated-internal-index-table-in-an-addon
2.	(No explanation yet) if bm.free() or bm.clear() at the end of main(), blender crashes
"""

def main():
	obj = bpy.context.active_object

	if obj.mode == 'OBJECT':
		bpy.ops.object.mode_set(mode='EDIT')
	
	bpy.ops.mesh.select_all(action='DESELECT')
	
	me = obj.data	
	bm = bmesh.from_edit_mesh(me)

	# show number of verts, edges, and faces and other properties/values
	detail(bm)

	# one time build only from set of equal resolution mesh circles to add faces along z
	add_side_faces(bm, 4, 32)

	detail(bm)

	selectv(bm, 0, 0)
	selecte(bm, 0, 0)
	selectf(bm, 0, 0)

	detail_loop(bm, 0)

	bmesh.update_edit_mesh(me)

def detail(bm):
	print('BM:')
	print(bm)
	print(dir(bm))
	print('EDGES:')
	print(len(bm.edges))
	print('VERTS:')
	print(len(bm.verts))
	print('FACES:')
	print(len(bm.faces))
	# print('LOOPS:')
	# print(len(bm.loops))
	# print(bm.loops)
	# print(dir(bm.loops))
	# print('LAYERS:')
	# print(bm.loops.layers)
	# print(dir(bm.loops.layers))
	
def selectv(bm, start, end):
	"""select mesh verts with vertex index in range [start, end]"""
	if hasattr(bm.verts, "ensure_lookup_table"): 
		bm.verts.ensure_lookup_table()

	if start == end:
		print('Vert #%d' % start)
		# print(dir(bm.verts[start]))
		print([edge for edge in bm.verts[start].link_edges])

	for vindex, vert in enumerate(bm.verts):
		if vindex < start:
			continue
		elif vindex > end:
			break
		# print(vindex, dir(vert))
		vert.select = True

def selecte(bm, start, end):
	"""select mesh edges with edge index in range [start, end]"""
	if hasattr(bm.edges, "ensure_lookup_table"):
		bm.edges.ensure_lookup_table()

	if start == end:
		print('Edge #%d' % start)
		# print(dir(bm.edges[start]))

	for eindex, edge in enumerate(bm.edges):
		if eindex < start:
			continue
		elif eindex > end:
			break
		# print(eindex, dir(edge))
		edge.select = True

def selectf(bm, start, end):
	"""select mesh faces with face index in range [start, end]"""
	if hasattr(bm.faces, "ensure_lookup_table"):
		bm.faces.ensure_lookup_table()

	if start == end:
		try:
			assert bm.faces[start].index == start
		except AssertionError:
			print('Face #%d and .index %d not match!' % (start, bm.faces[start].index))

		face = bm.faces[start]
		face.select_set(True)
		# print(dir(face))
		print('Face %s VERTS:' % start)
		print([vert for vert in face.verts])
		print('Face %s LOOPS:' % start)
		print([loop for loop in face.loops])

		return

	for findex, face in enumerate(bm.faces):
		if findex < start:
			continue
		elif findex > end:
			break
		print(dir(face))
		face.select_set(True)

def add_side_faces(bm, rings, resolution):
	"""
	works only for sets of equal resolution mesh circles to add faces along z
	"""
	if hasattr(bm.verts, "ensure_lookup_table"):
		bm.verts.ensure_lookup_table()

	for i in range(rings - 1):
		for j in range(resolution):
			offset = i * resolution
			verts = [j, (j + 1) % resolution, (j + 1) % resolution + resolution, j + resolution]
			verts = [index + offset for index in verts]
			try:
				face = bm.faces.new([bm.verts[i] for i in verts])
				# face.normal_update()
			except:
				print('Face error (already exists): %s' % verts)
				# for vert in verts:
				# 	bm.verts[vert].select_set(True)
	
	bm.normal_update()

def detail_loop(bm, face_index):
	"""exploit detail of a loop belonged to a certain face"""
	face = bm.faces[face_index]

	print('Face #%d has %d Loops' % (face_index, len(face.loops)))

	for lindex, loop in enumerate(face.loops):
		print('\tLoop #%d Angle %f Normal %s Tangent %s' % (lindex, loop.calc_angle(), loop.calc_normal(), loop.calc_tangent()))

if __name__ == "__main__":
	main()