import bpy
import os.path

from math import radians
from mathutils import Vector
from functools import wraps
from time import time
from bpy_extras.io_utils import ExportHelper

# ---------------- Addon Stuff ---------------- #

# Metadata for blender.
bl_info = {
    # required
    'name': 'HolderGenerator',
    'blender': (3, 0, 0),
    'category': 'Object',
    # optional
    'version': (1, 0, 0),
    'author': 'Gal Suchetzky',
    'description': 'Holder Generator Addon.',
}

# Types of hangers.
hanger_types = [
    ("TABLE", "Table", "", 1),
    ("RING", "Ring", "", 2),
    ("WALL", "Wall", "", 3),
]

# UI properties.
PROPS = [
    ('z_offset', bpy.props.IntProperty(name='Z offset', default=0)),
    ('shell_scaleup', bpy.props.FloatProperty(name='Shell Scaleup', default=1.05, min=1.0)),
    ('wall_thickness', bpy.props.FloatProperty(name='Wall Thickness', default=10, min=1)),
    ('hanger_rotation', bpy.props.IntProperty(name='Hanger Rotation', default=0, min=0, max=360)),
    ('hanger_type', bpy.props.EnumProperty(name='Hanger Type', items=hanger_types)),
    ('hanger_dir_path', bpy.props.StringProperty(name="Hanger Dir Path", description="Choose the directory with the hanger files.", default="", maxlen=1023, subtype='DIR_PATH')),
    
]


class HolderPanel(bpy.types.Panel):
    """
    Class for the panel itself. contains metadata on the class and the draw function that draws the UI panel.
    """    
    bl_idname = 'VIEW3D_PT_holder_generator_panel'
    bl_label = 'Holder Generator'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HolderGen'
    
    def draw(self, context):
        """
        Draws the UI panel.
        """
        col = self.layout.column()
        for (prop_name, _) in PROPS:
            row = col.row()
            row.prop(context.scene, prop_name)
        
        col.operator('opr.holder_generator_operator', text='Generate')
        col.operator('opr.reset_values_operator', text='Reset')
            
class HolderGeneratorOperator(bpy.types.Operator):
    """
    Operator to run the code.
    """
    bl_idname = 'opr.holder_generator_operator'
    bl_label = 'Holder Generator'
    
    def execute(self, context):
        """
        Executes the holder generator.
        """
        # Get the params from the UI.
        params = (
            context.scene.z_offset,
            context.scene.shell_scaleup,
            context.scene.wall_thickness,
            context.scene.hanger_rotation,
            context.scene.hanger_type,
            context.scene.hanger_dir_path
        )
        
        # Execute the holder generator.
        generate_holder(*params)
                    
        return {'FINISHED'}
    
class ResetValuesOperator(bpy.types.Operator):
    """
    Operator to reset the values of the panel.
    """
    bl_idname = 'opr.reset_values_operator'
    bl_label = 'Reset Values'
    
    def execute(self, context):
        """
        Resets all the values of the addon to their default values.
        """
        # Get the params from the UI.
        params = (
            context.scene.z_offset,
            context.scene.shell_scaleup,
            context.scene.wall_thickness,
            context.scene.hanger_rotation,
            context.scene.hanger_type,
            context.scene.hanger_dir_path
        )
        
        context.scene.property_unset("z_offset")
        context.scene.property_unset("shell_scaleup")
        context.scene.property_unset("wall_thickness")
        context.scene.property_unset("hanger_rotation")
        context.scene.property_unset("hanger_type")
#        context.scene.property_unset("hanger_dir_path")
                    
        return {'FINISHED'}



# Classes to register.
CLASSES = [
    HolderPanel,
    HolderGeneratorOperator,
    ResetValuesOperator,
]

def register():
    """
    Register the classes for the addon.
    This function is called when the addon is enabled.
    """
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.Scene, prop_name, prop_value)
        
    for c in CLASSES:
        bpy.utils.register_class(c)
        
    
def unregister():
    """
    Register the classes for the addon.
    This function is called when the addon is disabled.
    """
    for (prop_name, _) in PROPS:
        delattr(bpy.types.Scene, prop_name)
        
    for c in CLASSES:
        bpy.utils.unregister_class(c)
        
        
        
def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    """
    Display a message to the user.
    :param message: The message to display.
    :param title: The box title.
    :param icon: The icon of the message. Can be "INFO", "WARNING", "ERROR".
    """
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# ---------------- Logic Stuff ---------------- #
def timing(f):
    """
    Timing function, used for debugging.
    """
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
#        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kw, te-ts))
        print('time: %2.4f sec \t func:%r' % (te-ts, f.__name__))
        return result
    return wrap

@timing
def get_mins_maxs(target_object):
    """
    Calculates the min and max values for all axes.
    Used to speed up the calculations anywhere this information is required.
    """
    coords0 = target_object.matrix_world @ target_object.data.vertices[0].co
    max_x = coords0.x
    max_y = coords0.y
    max_z = coords0.z
    min_x = coords0.x
    min_y = coords0.y
    min_z = coords0.z
    
    for v in target_object.data.vertices:
        coords = target_object.matrix_world @ v.co
        max_x = max(coords.x, max_x)
        max_y = max(coords.y, max_y)
        max_z = max(coords.z, max_z)
        min_x = min(coords.x, min_x)
        min_y = min(coords.y, min_y)
        min_z = min(coords.z, min_z)
        
    return max_x, max_y, max_z, min_x, min_y, min_z


@timing
def copy(target_object):
    """
    Copy the active object in place.
    """
    bpy.ops.object.duplicate(linked=False)
    return bpy.context.active_object
    
    
@timing
def remove_over_xy_plane(target_object, z_offset, dimensions):
    """
    Removes the part of the target object that is above the XY plane.
    :param z_offset: the z value of the height to remove above.
    """
    max_x = max(abs(dimensions[0]), abs(dimensions[3])) + 10
    max_y = max(abs(dimensions[1]), abs(dimensions[4])) + 10
    max_z = max(dimensions[2], dimensions[5]) + 10

    # Add cube that covers the part of the model that is above the XY plane.
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, max_z + z_offset), scale=(max_x, max_y, max_z))
    boolean_cube = bpy.context.selected_objects[0]
    boolean_cube.name = 'boolean_cube'
    
    # Deselect all and set the active object to be the target again.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = target_object
    
    # Add a boolean modifier to the target object and set it to be the boolean cube.
    mod_bool = target_object.modifiers.new('Boolean', 'BOOLEAN')
    mod_bool.object = boolean_cube
    
    # Apply the modifier.
    bpy.ops.object.modifier_apply(modifier=target_object.modifiers[0].name)
    
    # Delete the boolean cube.
    bpy.ops.object.select_all(action='DESELECT')
    boolean_cube.select_set(True)
    bpy.ops.object.delete()
    
    
@timing  
def add_attach_port(target_object, z_offset, dimensions):
    """
    Adds an attach port location to the model.
    Should be used before the convex hull operation.
    """
    # Get max x to know where to put the port. + 1 to be a bit further.
    port_x = dimensions[0] + 1
    
    # Calculate the height of the port.
    port_height = abs(dimensions[5]) / 4
    
    # Calculate the port width.
    port_width = (dimensions[1] - dimensions[4]) / 4
    
    # Calculate the port y.
    port_y = (dimensions[1] + dimensions[4]) / 2
    
    # Add port cube.
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(port_x, port_y, -port_height/2 + z_offset), scale=(1, port_width, port_height))
    port_cube = bpy.context.selected_objects[0]
    port_cube.name = 'port_cube'
    
    # Rotate the port just a bit so it remains after removing the blocking faces.
    bpy.ops.transform.rotate(value=radians(-2), orient_axis='Y')
    
    # Deselect all and set the active object to be the target again.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = target_object
    
    # Add a boolean modifier to the target object, change it to union operation and set it to be the port cube.
    mod_bool = target_object.modifiers.new('Boolean', 'BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    mod_bool.object = port_cube

    # Apply the modifier.
    bpy.ops.object.modifier_apply(modifier=target_object.modifiers[0].name)
    
    # Delete the port cube.
    bpy.ops.object.select_all(action='DESELECT')
    port_cube.select_set(True)
    bpy.ops.object.delete()
    
    
@timing
def convex_hull(target_object):
    """
    Calculates the convex hull of the given target object.
    """
    # Set the target object to be the active object.
    bpy.context.view_layer.objects.active = target_object
    
    # Set the object to edit mode and calculate the convex hull 
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.mode_set(mode='OBJECT')


@timing
def delete_blocking_faces(target_object):
    """
    Deletes all faces with normals that are more than 90 degrees to the positive Z direction.
    Essentially, removing all faces that block the object from sliding straight up.
    """
    # Set the target object to be the active object.
    bpy.context.view_layer.objects.active = target_object
    
    # Get all bad faces.
    up = Vector((0, 0, 1))
    test_angle = radians(90)
    
    # List all faces with normal less than 90 degrees up.
    faces = [f.index for f in target_object.data.polygons
             if (target_object.rotation_euler.to_matrix() @ f.normal).angle(up) < test_angle]

    # Deselect everything.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    # Reselect the originally selected faces.
    bpy.ops.object.mode_set(mode='OBJECT')
    for face_idx in faces:
        target_object.data.polygons[face_idx].select = True
        
    # Delete selected faces.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # Reselect all.
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Change back to object mode.
    bpy.ops.object.mode_set(mode='OBJECT')


@timing
def thicken_shell(target_object, thickness):
    """
    Given a shell, extrudes it along the normals to thicken it.
    """
    # Set the target object to be the active object.
    bpy.context.view_layer.objects.active = target_object
    
    # Extrude along the normals.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":thickness, "use_even_offset":False, "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "release_confirm":True, "use_accurate":False})
    bpy.ops.object.mode_set(mode='OBJECT')


@timing    
def uniform_scale(target_object, s):
    """
    Scales the target object uniformly.
    """
    # Set scale for the target object to 1.1 of it's size.
    target_object.scale = (s, s, s)
        
def apply_subsurf_modifier(target_object):
    """
    Add subsurf modifier and apply it to to the target object.
    """
    mod_bool = target_object.modifiers.new('subsurf', 'SUBSURF')
    target_object.modifiers[0].levels = 2
    bpy.ops.object.modifier_apply(modifier=target_object.modifiers[0].name)


@timing
def get_attach_port_vertices(target_object, type, dimensions):
    """
    Selects the port vertices and returns them.
    use type to specify hanger or holder with HANGER, HOLDER.
    """
    
    # Deselect all vertices.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the 4 vertices. Note that if we calculate for the  hanger we don't want to reverse.
    vertices_tmp = sorted(target_object.data.vertices, reverse=type=='HOLDER', key=lambda v: (target_object.matrix_world @ v.co).x)
    
    if type == 'HANGER':
        vertices = vertices_tmp[:4]
    
    else:
        threshold = min(dimensions[0] - dimensions[3], dimensions[1] - dimensions[4]) / 5
        vertices = []
        for v in vertices_tmp:
            accepted = True
            for v0 in vertices:
                if (v.co - v0.co).length < threshold:
                    accepted = False
                    break
            if accepted:
                vertices.append(v)
                
            if len(vertices) == 4:
                break
        
    # Set the attach ports selected.
    for v in vertices:
        v.select = True
        
    return vertices


@timing
def import_hanger(type, hanger_rotation, hangers_dir_path):
    """
    imports the requested hanger.
    TABLE for table mount.
    WALL for wall mount.
    RING for cylinder mount.
    """
    # File paths for the hangers stls.
    
    hanger_file_paths = {
        "TABLE": hangers_dir_path + "clamp_frame.stl",
        "WALL": hangers_dir_path + "wall_mount.stl",
        "RING": hangers_dir_path + "ring_mount.stl"
    }
    
    # Import the stl.
    bpy.ops.import_mesh.stl(filepath=hanger_file_paths[type])
    
    # Keep the hanger object.
    hanger = bpy.context.active_object
    
    # Rotate the hanger on the X axis by the specified degrees.
    bpy.ops.transform.rotate(value=radians(hanger_rotation), orient_axis='X')

    return hanger


@timing
def connect_holder_hanger(holder, hanger):
    """
    Connects the holder and the hanger together.
    """
    # Join the holder and the hanger.
    holder.select_set(True)
    hanger.select_set(True)
    bpy.ops.object.join()
    
    # create the connecting arm.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.convex_hull()
    
    # Make manifold.
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.mesh.print3d_clean_non_manifold()
    
    # Change back to object mode.
    bpy.ops.object.mode_set(mode='OBJECT')


@timing
def generate_holder(z_offset = 0, shell_scaleup = 1.05, wall_thickness = 10, hanger_rotation = 0, hanger_type = "TABLE", hanger_dir_path=""):
    """
    Runs the logic of the program.
    :param z_offset: The offset from the z=0 plane where above it the hanger will not be created.
    :param shell_scaleup: How much to scale up the shell to have space for the object. Shouldn't be smaller than 1. the bigger it is the more space the object will have.
    :param wall_thickness: The thickness of the shell wall. Will determine how strong the holder is.
    :param hanger_rotation: X rotation of the hanger (to hang on tables or cylinders with different angles).
    :param hanger_type: The type of the hanger to use. shoud be on of {TABLE, RING, WALL}
    """
    # Make sure that the hangers folder is selected.
    if not hanger_dir_path:
        ShowMessageBox("Please select the folder that contains the hanger files. It came with the git repo you cloned.", "Hanger Directory Not Selected", 'ERROR')
        return
    
    # Check that a target object is selected.
    if not bpy.context.active_object:
        ShowMessageBox("Please select the object you would like to generate a holder for.", "Target Object Not Selected", 'ERROR')
        return
    
    # Check that the addon 3D print toolbox is installed.
    if 'object_print3d_utils' not in bpy.context.preferences.addons.keys():
        ShowMessageBox("Please install the addon mesh:3D-print-toolbox from the addon preferences.", "3D-print-toolbox not installed", 'ERROR')
        return
    
    # Save target object.
    limit_object = bpy.context.active_object
    
    # Copy the target object.
    holder = copy(limit_object)
    
    # Get the dimensions.
    dimensions = get_mins_maxs(holder)

    # Remove a part from the top, where we dont want the holder to form.
    remove_over_xy_plane(holder, z_offset, dimensions)
    
    # Get the dimensions.
    dimensions = get_mins_maxs(holder)
    
    # boolean a connection port to the object.
    add_attach_port(holder, z_offset, dimensions)
    
    # Calculate the convex hull.
    convex_hull(holder)
    
    # Remove all faces that restrict the object from being pulled straight up.
    delete_blocking_faces(holder)
    
    # Scale the shell a bit.
    uniform_scale(holder, shell_scaleup)
    
    # Thicken the shell to create walls.
    thicken_shell(holder, wall_thickness)
    
    # Get the attach port vertices.
    port_vertices = get_attach_port_vertices(holder, 'HOLDER', dimensions)
    
    # Import the hanger of the specified type.
    hanger = import_hanger(hanger_type, hanger_rotation, hanger_dir_path)
    
    # Get the attach port vertices.
    port_vertices = get_attach_port_vertices(hanger, 'HANGER', dimensions)
    
    # Connect the holder and the hanger with a connecting arm.
    connect_holder_hanger(holder, hanger)
    

if __name__ == '__main__':
#    generate_holder()
    register()