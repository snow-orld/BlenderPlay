import bpy
import bmesh
import mathutils

obj = bpy.context.scene.objects.active
me = obj.data
bm = bmesh.from_edit_mesh(me)

edges_to_remove = []
is_vindex_in_order = True

# delete all edges that is not a boundary (linked faces auto removed)
if bm.faces:
    print('Removing all internal faces and edges')
    for edge in bm.edges:
        if not edge.is_boundary:
            edges_to_remove.append(edge)

    for edge in edges_to_remove:
        bm.edges.remove(edge)

if not bm.faces:
    # with only boundary edge left, wave them to faces
    for vindex, vert in enumerate(bm.verts):
        #print(vindex, vert)
        if vindex != vert.index:
            is_vindex_in_order = False
            break

    if is_vindex_in_order:
        # wave
        # v1 - v0
        #  | - |
        # v3 - v2
        for vert in bm.verts:
            if vert.index % 2:
                continue
            v0 = vert
            v1 = bm.verts[(vert.index + 1) % len(bm.verts)]
            v2 = bm.verts[(vert.index + 2) % len(bm.verts)]
            v3 = bm.verts[(vert.index + 3) % len(bm.verts)]
            bm.faces.new([v0, v1, v3, v2])

    else:
        print('Error: Cannot wave according to vertex index, out of order')
        raise RuntimeError('Cannot wave according to vertex index, out of order')

bm.normal_update()
bmesh.update_edit_mesh(me)