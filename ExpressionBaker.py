bl_info = {
    "name": "Expression Baker",
    "author": "Victor Do",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Expression Baker",
    "description": "Captures a rest pose and creates a clean expression shape key from the difference.",
    "warning": "",
    "doc_url": "",
    "category": "Animation",
}

import bpy
import numpy as np

# A global dictionary to store the rest pose data for objects
# The key will be the object name, the value will be the vertex coordinates
rest_pose_data = {}

class EXPRESSION_BAKER_OT_capture_rest_pose(bpy.types.Operator):
    """Captures the current vertex positions of the active object as the rest pose"""
    bl_idname = "expression_baker.capture_rest_pose"
    bl_label = "Capture Rest Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        
        if not obj.data.vertices:
            self.report({'WARNING'}, "Object has no vertices to capture.")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        
        num_verts = len(eval_obj.data.vertices)
        # Store a flattened numpy array of vertex coordinates in world space
        coords = np.empty(num_verts * 3, dtype=np.float32)
        eval_obj.data.vertices.foreach_get("co", coords)
        
        rest_pose_data[obj.name] = coords
        
        self.report({'INFO'}, f"Rest pose captured for '{obj.name}'")
        return {'FINISHED'}


class EXPRESSION_BAKER_OT_create_expression_key(bpy.types.Operator):
    """Creates a new shape key from the difference between the rest pose and the current pose"""
    bl_idname = "expression_baker.create_expression_key"
    bl_label = "Create Expression Shape Key"
    bl_options = {'REGISTER', 'UNDO'}
    
    new_shape_key_name: bpy.props.StringProperty(
        name="Shape Key Name",
        default="Expression"
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.name in rest_pose_data)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        
        if obj.name not in rest_pose_data:
            self.report({'ERROR'}, "No rest pose captured. Please capture a rest pose first.")
            return {'CANCELLED'}
            
        rest_coords_flat = rest_pose_data[obj.name]

        depsgraph = context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        
        num_verts = len(eval_obj.data.vertices)
        current_coords_flat = np.empty(num_verts * 3, dtype=np.float32)
        eval_obj.data.vertices.foreach_get("co", current_coords_flat)
        
        if len(rest_coords_flat) != len(current_coords_flat):
            self.report({'ERROR'}, "Vertex count has changed since capturing rest pose. Please re-capture.")
            del rest_pose_data[obj.name]
            return {'CANCELLED'}

        # Create shape keys if they don't exist, starting with Basis
        if obj.data.shape_keys is None:
            obj.shape_key_add(name="Basis")
            
        new_key = obj.shape_key_add(name=self.new_shape_key_name, from_mix=False)

        # 1. Reshape flat arrays to (N, 3) arrays of vectors
        # --- Vectorized Calculation ---
        rest_coords = rest_coords_flat.reshape(-1, 3)
        current_coords = current_coords_flat.reshape(-1, 3)
        # 2. Calculate the difference (delta) in world space for all vertices at once
        world_deltas = current_coords - rest_coords
        # 3. Get the inverse of the object's world matrix to transform deltas from world to local space
        #    We convert the Blender matrix to a NumPy array to solve the TypeError
        mat_world_to_local_3x3 = np.array(obj.matrix_world.inverted().to_3x3())
        # 4. Apply the transformation to all deltas in a single batch operation.
        #    (V @ M.T is the NumPy equivalent of M @ V for a batch of vectors V)
        local_deltas = world_deltas @ mat_world_to_local_3x3.T

        # 5. Get the first key by index (0) instead of by name
        # This makes the script independent of the basis key's name.
        basis_key = obj.data.shape_keys.key_blocks[0]
        
        basis_coords_flat = np.empty(num_verts * 3, dtype=np.float32)
        basis_key.data.foreach_get("co", basis_coords_flat)
        basis_coords = basis_coords_flat.reshape(-1, 3)
        
        # 6. The new shape key's positions are the Basis positions plus the calculated local deltas
        final_coords = basis_coords + local_deltas

        # 7. Apply the calculated positions to the new shape key
        new_key.data.foreach_set("co", final_coords.ravel())
        
        self.report({'INFO'}, f"Created shape key '{self.new_shape_key_name}'")
        return {'FINISHED'}


class EXPRESSION_BAKER_PT_panel(bpy.types.Panel):
    """Creates a Panel in the 3D View Sidebar"""
    bl_label = "Expression Baker"
    bl_idname = "OBJECT_PT_expression_baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Expression Baker'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.type == 'MESH':
            if obj.name in rest_pose_data:
                layout.label(text=f"Rest pose captured for: {obj.name}", icon='CHECKMARK')
            else:
                layout.label(text="No rest pose captured.", icon='ERROR')
            
            row = layout.row()
            row.operator(EXPRESSION_BAKER_OT_capture_rest_pose.bl_idname)
            
            row = layout.row()
            row.enabled = obj.name in rest_pose_data
            row.operator(EXPRESSION_BAKER_OT_create_expression_key.bl_idname)
        else:
            layout.label(text="Select a Mesh object.", icon='INFO')

# --- Registration ---
classes = (
    EXPRESSION_BAKER_OT_capture_rest_pose,
    EXPRESSION_BAKER_OT_create_expression_key,
    EXPRESSION_BAKER_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    rest_pose_data.clear()

if __name__ == "__main__":
    register()