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

# *********** operators used in track tool ***************

class TrackTool_Operator_Align2XYPlane(Operator):
    """ This operator brings all control points in the bezier curve onto xy plane, i.e. zeror all zs"""
    bl_idname = "curve.align_to_xy_plane"
    bl_label = "Align to XY Plane"
    bl_options = {"REGISTER","UNDO"}

    def align(self, obj):
        if obj.type == 'CURVE':
            for spline in obj.data.splines:
                if spline.type == 'BEZIER':
                    for p in spline.bezier_points:
                        p.co.z = 0
                        p.handle_right.z = 0
                        p.handle_left.z = 0
                else:
                    for p in spline.points:
                        p.co.z = 0

    def execute(self, context):
        obj = context.active_object
        scene = context.scene

        if obj and obj.select:
            self.align(obj)

        return {'FINISHED'}

class TrackTool_Operator_SmoothElevation(Operator):
    """This operator changes types of all control points except the start and end of a bezier curve to 'automatic' to get smooth elevation change """
    bl_idname = "curve.smooth_elevation"
    bl_label = "Smooth Elevation"
    bl_options = {"REGISTER","UNDO"}

    def smooth(self, obj):
        if obj.type != 'CURVE':
            return

        for spline in obj.data.splines:
            if (spline.type == 'BEZIER'):
                for i in range(len(spline.bezier_points) - 1)[1:]:
                    p = spline.bezier_points[i]
                    handle_left_type = p.handle_left_type
                    handle_right_type = p.handle_right_type
                    p.handle_left_type = 'AUTO'
                    p.handle_right_type = 'AUTO'
                    p.handle_left_type = 'ALIGNED'
                    p.handle_right_type = 'ALIGNED'

    def execute(self, context):
        obj = context.active_object
        if obj and obj.select:
            self.smooth(obj)

        return {'FINISHED'}

class TrackTool_Operator_Convert2Mesh(Operator):
    """This operator conver the beveled bezier curve to a mesh, meanwhile caculating uv map as a strip along central line"""
    bl_idname = "curve.convert_to_mesh"
    bl_label = "Reference Line Convert to Mesh"
    bl_options = {"REGISTER","UNDO"}

    def calculate_uv(self, obj):
        # !important. need to generate uv for mesh as physics tanget space along a track
        for face in obj.data.loops:
            print(face)
        pass

    def convert(self, obj):
        if obj.type == 'CURVE' and obj.data.bevel_object:
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='TOGGLE')
            self.calculate_uv(obj)

    def execute(self, context):
        obj = context.active_object
        if obj and obj.select:
            self.convert(obj)

        return {'FINISHED'}

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
        layout.operator("curve.align_to_xy_plane", text="Project to X-Y Plane")
    
    @staticmethod
    def draw_smooth_elevation(layout, label=False):
        if label:
            layout.label(text="Smooth Handle")
        layout.operator("curve.smooth_elevation", text="Smooth Handle Direction", icon="SMOOTHCURVE")

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

class TrackTool_Panel_Mesh(TrackToolPanel, Panel):
    bl_label = "Mesh"
    #bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curve.convert_to_mesh", text="Convert to Mesh", icon="MESH_DATA")
        col.operator("curve.convert_to_mesh", text="Edit UV", icon="MATSPHERE")


def register():
    bpy.utils.register_class(TrackTool_Operator_Align2XYPlane)
    bpy.utils.register_class(TrackTool_Operator_SmoothElevation)
    bpy.utils.register_class(TrackTool_Operator_Convert2Mesh)

    bpy.utils.register_class(TrackTool_Panel_RefernceLine)
    bpy.utils.register_class(TrackTool_Panel_Mesh)

def unregister():
    bpy.utils.unregister_class(TrackTool_Operator_Align2XYPlane)
    bpy.utils.unregister_class(TrackTool_Operator_SmoothElevation)
    bpy.utils.unregister_class(TrackTool_Operator_Convert2Mesh)

    bpy.utils.unregister_class(TrackTool_Panel_RefernceLine)
    bpy.utils.unregister_class(TrackTool_Panel_Mesh)

if __name__ == "__main__":
    register()