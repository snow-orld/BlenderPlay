# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
     "name": "Track Tools",
     "version": (1, 0),
     "blender": (2, 7, 8),
     "location": "VIEW 3D > Tools > Track Building Tool ",
     "description": "Tools for building tracks for Speed Supernova Kart Project",
     "warning": "For Internal Development Only",
     "wiki_url": "",
     "tracker_url": "",
     "category": "Mesh"}

#Imports:
import bpy
from bpy.types import Operator, Menu, Panel, UIList
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from mathutils import Vector
from math import floor
import bmesh
from numpy import *

# *********** operators used in track tool ***************

class TrackTool_Operator_Align2XYPlane(Operator):
    """Brings all control points in the bezier curve onto xy plane"""
    bl_idname = "track.align_to_xy_plane"
    bl_label = "Align to XY Plane"
    bl_options = {"REGISTER","UNDO"}

    def align(self, obj):
        if obj.type == 'CURVE':
            obj.location.z = 0
            for spline in obj.data.splines:
                if spline.type == 'BEZIER':
                    for p in spline.bezier_points:
                        p.handle_left_type = 'FREE'
                        p.handle_right_type = 'FREE'
                        p.co.z = 0
                        p.handle_right.z = 0
                        p.handle_left.z = 0
                        p.handle_left_type = 'ALIGNED'
                        p.handle_right_type = 'ALIGNED'
                else:
                    for p in spline.points:
                        p.co.z = 0

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'CURVE' and obj.data.splines[0].type == 'BEZIER'

    def execute(self, context):
        obj = context.active_object
        self.align(obj)
        return {'FINISHED'}

class TrackTool_Operator_InterpolateElevation(Operator):
    """Select control points in edit mode to smooth the elevation between start and end of the selected"""
    bl_idname = "track.interpolate_elevation"
    bl_label = "Smooth Elevation"
    bl_options = {"REGISTER","UNDO"}

    # All handles set to AUTO then back will change curve's plan-view shape - not work for all 
    # Interpolate only z between two selected points to guarantee a smotth elevation! - works only for sampled curve
    def smooth(self, obj):
        selected, spline = self.getSelectedPoints(obj)
        
        if selected is None:
            self.report({"ERROR"}, "Selected control points are not consecutive in one spline.")
            return

        loop_count = len(spline.bezier_points)
        # selected is in the order of bezpoints from 0, need to rearrange it from the two ends fo the selected range
        # Only two cases: 1.the gap is in between the dictionary elements, 2. the gap is just between the end and start of the dic elements
        keylist = []
        for key in selected:
            keylist.append(key)
        start_index = keylist[0]
        end_index = keylist[-1]
        prev_index = start_index
        for key in keylist[1:]:
            if (key - prev_index) % loop_count > 1:
                start_index = key
                end_index = prev_index
            prev_index = key

        print('Seletec smoothing range starts from %d to %d' % (start_index, end_index))

        # start and end point should have smooth handle on x-y plane
        z_total_diff = selected[end_index].co.z - selected[start_index].co.z
        s_offset = 0
        no_handles = []
        distance = [0]
        for i in range(len(selected)):
            prev_index = (start_index + i - 1) % loop_count
            current_index = (start_index + i) % loop_count
            no_handles.append(self.has_no_handle(selected[current_index]))
            if i == 0:
                continue
            s_offset += self.getProjectedDistance(selected[prev_index], selected[current_index], spline.resolution_u)
            distance.append(round(s_offset, 4))
        for i in range(len(selected)):
            if i == 0 or i == len(selected) - 1:
                continue
            prev_index = (start_index + i - 1) % loop_count
            current_index = (start_index + i) % loop_count
            post_index = (start_index + i + 1) % loop_count
            p = selected[current_index]
            p.handle_left_type = 'FREE'
            p.handle_right_type = 'FREE'
            p.co.z = selected[start_index].co.z + distance[i] / distance[-1] * z_total_diff

            if no_handles[i]:
                p.handle_left.z = p.co.z
                p.handle_right.z = p.co.z
            
            p.handle_left_type = 'ALIGNED'
            p.handle_right_type = 'ALIGNED'

    def has_no_handle(self, bezpoint):
        return (bezpoint.handle_left - bezpoint.co).length < 1E-4 and (bezpoint.handle_right - bezpoint.co).length < 1E-4

    # Tell if control point selected - if one handle of a control point is selected, the control point is selected
    def is_selected(self, bezpoint):
        return bezpoint.select_control_point or bezpoint.select_left_handle or bezpoint.select_right_handle

    # Get Selected control points, valid only when selected control points are neighbors to one another
    def getSelectedPoints(self, obj):
        # Return empty dictionary<index, bezpoint> if not valid
        selected = {}
        find_selected_in_prev_spline = False
        in_spline = None
        for spline in obj.data.splines:
            if spline.type == 'BEZIER':
                last_selected_point_index = -1
                find_selected_in_cur_spline = False
                isolated_selected_gap_count = 0
                for i in range(len(spline.bezier_points)):
                    p = spline.bezier_points[i]
                    if self.is_selected(p):
                        if not find_selected_in_cur_spline:
                            find_selected_in_cur_spline = True
                            in_spline = spline
                        if find_selected_in_prev_spline:
                            break
                        if isolated_selected_gap_count > 1:
                            break
                        last_selected_point_index = i
                        selected[i] = p
                    else:
                        # if p is not selected but its circular presessor is selected
                        if find_selected_in_cur_spline and (i - last_selected_point_index) % len(spline.bezier_points) == 1:
                            isolated_selected_gap_count += 1

                # print(isolated_selected_gap_count, find_selected_in_cur_spline, find_selected_in_prev_spline)
                if isolated_selected_gap_count > 1:
                    selected.clear()
                    break

                if find_selected_in_cur_spline and find_selected_in_prev_spline:
                    selected.clear()
                    break

                if find_selected_in_cur_spline and not find_selected_in_prev_spline:
                    find_selected_in_prev_spline = True

        return (selected, in_spline) if len(selected) > 1 else (None, None)

    # Get distance on x-y plane between two control points according to their resolution
    def getProjectedDistance(self, bezpoint1, bezpoint2, resolution):
        p0 = bezpoint1.co.copy(); p0.z = 0
        p1 = bezpoint1.handle_right.copy(); p1.z = 0
        p2 = bezpoint2.handle_left.copy(); p2.z = 0
        p3 = bezpoint2.co.copy(); p3.z = 0
        prepoint = p0
        distance = 0
        for t in linspace(0, 1, resolution + 1):
            point = (1-t)*(1-t)*(1-t)*p0 + 3*(1-t)*(1-t)*t*p1 + 3*(1-t)*t*t*p2 + t*t*t*p3
            distance += linalg.norm(point - prepoint)
            prepoint = point
        return distance

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.mode == 'EDIT' and obj.type == 'CURVE' and obj.data.splines[0].type == 'BEZIER' and obj.data.splines[0].use_cyclic_u

    def execute(self, context):
        obj = context.active_object
        self.smooth(obj)
        return {'FINISHED'}

class TrackTool_Operator_Sample2Poly(Operator):
    """This operator samples a bezier curve to fixed resolution polyline spline"""
    bl_idname = "track.sample_to_poly"
    bl_label = "Sample Bezier to Poly"
    bl_options = {"REGISTER","UNDO"}

    resolution = bpy.props.IntProperty(name="Resolution", default=2, min=1, max=100)

    def sample(self, obj):
        if bpy.data.objects.find(obj.name + '_sampled') == -1:
            curve = bpy.data.curves.new(name=obj.name + '_sampled', type='CURVE')
            curve.dimensions = '3D'
            newobj = bpy.data.objects.new(obj.name + '_sampled', curve)
            newobj.location = obj.location
            bpy.context.scene.objects.link(newobj)

        sampledobj = bpy.data.objects[obj.name + '_sampled']
        # sampledobj.select = True
        # obj.select = False
        # obj.hide = True
        # bpy.context.scene.objects.active = sampledobj
        sampledobj.data.bevel_object = obj.data.bevel_object
        sampledobj.data.twist_mode = 'Z_UP'
        self.resolution = obj.data.resolution_u

        #clean sampledobj's spline
        self.cleanSplines(sampledobj)

        #get sampled points for central line
        for spline in obj.data.splines:
            points = self.getSamplePoints(spline)
            polyline = self.addSpline(sampledobj, points)
            polyline.use_cyclic_u = spline.use_cyclic_u

    def cleanSplines(self, obj):
        if (len(obj.data.splines)):
            for spline in obj.data.splines:
                obj.data.splines.remove(spline)

    def addSpline(self, obj, points):
        polyline = obj.data.splines.new('POLY')
        polyline.points.add(len(points) - 1)

        for i in range(len(points)):
            x, y, z = points[i]
            polyline.points[i].co = (x, y, z, 1)

        return polyline

    def bezier(self, p0, p1, p2, p3, resolution):
        points = []
        # in design phase, two ends of a straight line get their handles sitting together with control points
        # may be not sufficient valid for all cases, let's wait for bugs to appear
        if (p1 - p0).length < 1E-4 and (p3 - p2).length < 1E-4:
            points.append(p0)
            points.append(p3)
        else:    
            for t in linspace(0, 1, resolution + 1):
                point = (1-t)*(1-t)*(1-t)*p0 + 3*(1-t)*(1-t)*t*p1 + 3*(1-t)*t*t*p2 + t*t*t*p3
                points.append(point)
        return points

    def getSamplePoints(self, spline):
        points = []

        for index in range(len(spline.bezier_points) - 1):

            ctrlPnt = spline.bezier_points[index]
            nextPnt = spline.bezier_points[index + 1]

            if index == 0:
                points += self.bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, self.resolution)
            else:
                points += self.bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, self.resolution)[1:]

        if spline.use_cyclic_u:

            ctrlPnt = spline.bezier_points[len(spline.bezier_points) - 1]
            nextPnt = spline.bezier_points[0]

            points += self.bezier(ctrlPnt.co, ctrlPnt.handle_right, nextPnt.handle_left, nextPnt.co, self.resolution)[1:-1]

        return points

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'CURVE' and obj.data.splines[0].type == 'BEZIER'

    def execute(self, context):
        obj = context.active_object
        self.sample(obj)

        return {'FINISHED'}

class TrackTool_Operator_GenerateRoad(Operator):
    """Generate a straight line as road cross section"""
    bl_idname = "track.generate_road_cross_section"
    bl_label = "Generate Road Cross Section"
    bl_options = {"REGISTER","UNDO"}

    width = FloatProperty(
        name = "width",
        description = "width of the road crosssection",
        min = 1.0, max = 100.0,
        default = 10.0)

    def generate(self, obj, width):
        if bpy.data.objects.find('CrossSection') == -1:
            curve = bpy.data.curves.new(name='CrossSection', type='CURVE')
            curve.dimensions = '3D'
            newobj = bpy.data.objects.new('CrossSection', curve)
            newobj.location = Vector((0,0,0))
            bpy.context.scene.objects.link(newobj)

        targetobj = bpy.data.objects['CrossSection']

        #Clean CrossSection data
        for spline in targetobj.data.splines:
            targetobj.data.splines.remove(spline)

        poly = targetobj.data.splines.new('POLY')
        poly.points.add(1)
        poly.points[0].co = (self.width / 2, 0, 0, 1)
        poly.points[1].co = (-self.width / 2, 0, 0, 1)

        if obj.data.bevel_object == None:
            obj.data.bevel_object = bpy.data.objects['CrossSection']

        if obj.data.twist_mode != 'Z_UP':
            obj.data.twist_mode = 'Z_UP'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'CURVE'

    def execute(self, context):
        obj = context.active_object
        self.generate(obj, self.width)
        return {'FINISHED'}

class TrackTool_Operator_Convert2Mesh(Operator):
    """Convert the beveled bezier curve to a mesh, meanwhile caculating uv map as a strip along central line"""
    bl_idname = "track.convert_to_mesh"
    bl_label = "Reference Line Convert to Mesh"
    bl_options = {"REGISTER","UNDO"}

    
    def convert(self, obj):
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        for v in obj.data.vertices:
            v.select = True

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'CURVE' and obj.data.splines[0].type == 'BEZIER' and obj.data.bevel_object != None

    def execute(self, context):
        obj = context.active_object
        self.convert(obj)
        return {'FINISHED'}

class TrackTool_Operator_EditUV(Operator):
    """Calculate UV in track-coordinates"""
    bl_idname = "track.edit_uv"
    bl_label = "Edit UV"
    bl_options = {"REGISTER","UNDO"}

    def calculate_uv(self, obj):
        # !important. need to generate uv for mesh as physics tanget space along a track
        if obj.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(obj.data)

        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.layers.tex.verify()    # currently blender needs both layers.

        # accumulative s in track coordinate for v
        s = 0
        # get width of the road
        width = (obj.data.vertices[1].co - obj.data.vertices[0].co).length
        width = round(width, 4)

        # adjust UVs
        for face in bm.faces:
            vertices = {}
            for loop in face.loops:
                luv = loop[uv_layer]
                vertex_index = loop.vert.index
                vertices[vertex_index] = luv
                # v = floor(vertex_index / 2)
                # if vertex_index > v * 2:
                #     u = 1
                # else:
                #     u = 0
                # luv.uv = Vector((u, v))
            vertex_indices = sorted(vertices.keys())
            mid0 = (obj.data.vertices[vertex_indices[0]].co + obj.data.vertices[vertex_indices[1]].co) * 0.5
            mid1 = (obj.data.vertices[vertex_indices[-2]].co + obj.data.vertices[vertex_indices[-1]].co) * 0.5
            length = (mid1 - mid0).length

            for i in range(len(vertex_indices)):
                if i < 2:
                    vertices[vertex_indices[i]].uv = Vector((width if i % 2 else 0, s))
                else:
                    vertices[vertex_indices[i]].uv = Vector((width if i % 2 else 0, s + length))
            s += length

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.mesh.select_all(action='SELECT')

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        self.calculate_uv(obj)
        return {'FINISHED'}

# under construction
class TrackTool_Operator_Curve_ProportionalEdit(Operator):
    """Custom Proportional Edit with Custom Cut-Off Curves"""
    bl_idname = "track.curve_only_pe"
    bl_label = "Custom Proportional Edit"
    bl_context = "EDIT"
    bl_options = {"REGISTER","UNDO"}

    def __init__(self):
        print("Custom PE Start")

    def __del__(self):
        print("Custom PE End")

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.mode == 'EDIT'

    def execute(self, context):
        print(context.object.location)
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':   # Apply
            # self.value = event.mouse_x
            self.execute(context)
        elif event.type == 'LEFTMOUSE': # Confirm
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:   # Cancel
            context.object.location = self.init_loc_x
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc = context.object.location
        self.value = event.mouse_x
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

def drawLine(start, end, location):

    if bpy.data.objects.find('helper') == -1:
        curve = bpy.data.curves.new(name='helper', type='CURVE')
        curve.dimensions = '3D'

        obj = bpy.data.objects.new('helper', curve)
        obj.location = location
        bpy.context.scene.objects.link(obj)

    obj = bpy.data.objects['helper']
    testline = obj.data.splines.new('POLY')
    testline.points.add(1)
    testline.points[0].co = (start.x, start.y, start.z, 1)
    testline.points[1].co = (end.x, end.y, end.z, 1)

class TrackTool_Operator_Helper_Bezier_Handles(Operator):
    """Examine the hanles' coordinates along with control points' coordinates"""
    bl_idname = "curve.bezier_detail"
    bl_label = "Bezier Handles' Coordinates"
    bl_options = {"REGISTER","UNDO"}

    def examine(self, obj):
        for i in range(len(obj.data.splines)):
            spline = obj.data.splines[i]
            print('\n===================== Spline #' + str(i) + " =======================")
            for j in range(len(spline.bezier_points)):
                p = spline.bezier_points[j]
                print('\nBezier Point ' + str(j))
                print('control_point %s\nhandle_left %s (%s)\nhandle_right %s (%s)' % \
                    (p.co, p.handle_left, p.handle_left_type, p.handle_right, p.handle_right_type))
                if (p.co - p.handle_left).length < 1E-4:
                    print('NO LEFT HANDLE')
                if (p.co - p.handle_right).length < 1E-4:
                    print('NO RIGHT HANDLE')

    @classmethod
    def poll(self, context):
        obj = context.object
        return obj and obj.select and obj.type == 'CURVE' and obj.data.splines[0].type == 'BEZIER'

    def execute(self, context):
        obj = context.active_object
        self.examine(obj)
        return {'FINISHED'}

class TrackTool_Operator_Helper_Mesh_Detail(Operator):
    """Exploit the mesh loop's index and its vertex index in a multi-polygon mesh"""
    bl_idname = "mesh.loop_detail"
    bl_label = "Mesh Polygon and Vertex Realtion"
    bl_options = {"REGISTER","UNDO"}

    def examine(self, obj):
        if obj.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(obj.data)

        # exploit edge face loop
        bpy.ops.mesh.select_all(action='DESELECT')
        for face in bm.faces:
            print(face.index)
            face.select = True
            for vert in face.verts:
                # vert.select = True
                print('face #%d: %s' % (face.index, vert))

            if face.index > 0:
                break

        bmesh.update_edit_mesh(obj.data)

    @classmethod
    def poll(self, context):
        obj = context.object
        return obj and obj.select and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        self.examine(obj)
        return {'FINISHED'}

# *********** I/O for track tool *************************


# *********** tools panel for track tool *****************

class TrackToolPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Track Tools"

# ********** default tools for object-mode ****************

class TrackTool_Panel_RefernceLine(TrackToolPanel, Panel):
    bl_label = "Reference Line"
    # bl_context = "objectmode"

    @staticmethod
    def draw_add_curve(layout, label=False):
        if label:
            layout.label(text="Bezier")
        layout.operator("curve.primitive_bezier_curve_add", text="Bezier", icon="CURVE_BEZCURVE")
        layout.operator("curve.primitive_bezier_circle_add", text="Circle", icon='CURVE_BEZCIRCLE')

    @staticmethod
    def draw_to_xy_plane(layout, label=False):
        if label:
            layout.label(text="Align:")
        layout.operator("track.align_to_xy_plane", text="Project to X-Y Plane")
    
    @staticmethod
    def draw_smooth_elevation(layout, label=False):
        if label:
            layout.label(text="Interpolate Elevation")
        layout.operator("track.interpolate_elevation", text="Interpolate Elevation", icon="SMOOTHCURVE")

    @staticmethod
    def draw_road_cross_section(layout, label=False):
        if label:
            layout.label(text="Road Surface")
        layout.operator("track.generate_road_cross_section", text="Create Road Surface")

    @staticmethod
    def draw_sample_curve(layout, label=False):
        if label:
            layout.label(text="Sample Bezier Curve")
        layout.operator("track.sample_to_poly", text="Sample To Polyline")

    @staticmethod
    def draw_proportion_edit(layout, label=False):
        if label:
            layout.label(text="Curve Only Proporitonal Edit")
        layout.operator("track.curve_only_pe")

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Add Curve:")
        self.draw_add_curve(col)
        
        col = layout.column(align=True)
        col.label(text="Align:")
        self.draw_to_xy_plane(col)

        col = layout.column(align=True)
        col.label(text="Elevation:")
        self.draw_smooth_elevation(col)

        col = layout.column(align=True)
        col.label(text="Surface:")
        self.draw_road_cross_section(col)

        col = layout.column(align=True)
        col.label(text="Sample:")
        self.draw_sample_curve(col)

        # col = layout.column(align=True)
        # col.label(text="Edit:")
        # self.draw_proportion_edit(col)

class TrackTool_Panel_Mesh(TrackToolPanel, Panel):
    bl_label = "Mesh"
    #bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.operator("track.convert_to_mesh", text="Convert to Mesh", icon="MESH_DATA")
        col.operator("track.edit_uv", text="Edit UV", icon="MATSPHERE")

class TrackTool_Panel_Helper(TrackToolPanel, Panel):
    bl_label = "Helper"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column(align=True)
        col.operator("curve.bezier_detail", text="Bezier Detail", icon="CURVE_BEZCURVE")


        row = layout.row()
        col = row.column(align=True)
        col.operator("mesh.loop_detail", text="Mesh Detail", icon="MESH_DATA")

def register():
    bpy.utils.register_class(TrackTool_Operator_Align2XYPlane)
    bpy.utils.register_class(TrackTool_Operator_InterpolateElevation)
    bpy.utils.register_class(TrackTool_Operator_Sample2Poly)
    bpy.utils.register_class(TrackTool_Operator_GenerateRoad)
    bpy.utils.register_class(TrackTool_Operator_Curve_ProportionalEdit)
    bpy.utils.register_class(TrackTool_Operator_Convert2Mesh)
    bpy.utils.register_class(TrackTool_Operator_EditUV)

    bpy.utils.register_class(TrackTool_Panel_RefernceLine)
    bpy.utils.register_class(TrackTool_Panel_Mesh)

    # helper
    bpy.utils.register_class(TrackTool_Operator_Helper_Bezier_Handles)
    bpy.utils.register_class(TrackTool_Operator_Helper_Mesh_Detail)

    bpy.utils.register_class(TrackTool_Panel_Helper)

def unregister():
    bpy.utils.unregister_class(TrackTool_Operator_Align2XYPlane)
    bpy.utils.unregister_class(TrackTool_Operator_InterpolateElevation)
    bpy.utils.unregister_class(TrackTool_Operator_Sample2Poly)
    bpy.utils.unregister_class(TrackTool_Operator_GenerateRoad)
    bpy.utils.unregister_class(TrackTool_Operator_Curve_ProportionalEdit)
    bpy.utils.unregister_class(TrackTool_Operator_Convert2Mesh)
    bpy.utils.unregister_class(TrackTool_Operator_EditUV)

    bpy.utils.unregister_class(TrackTool_Panel_RefernceLine)
    bpy.utils.unregister_class(TrackTool_Panel_Mesh)

    # helper
    bpy.utils.unregister_class(TrackTool_Operator_Helper_Bezier_Handles)
    bpy.utils.unregister_class(TrackTool_Operator_Helper_Mesh_Detail)

    bpy.utils.unregister_class(TrackTool_Panel_Helper)

if __name__ == "__main__":
    register()