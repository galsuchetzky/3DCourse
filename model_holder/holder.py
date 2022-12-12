import bpy
from math import radians
from mathutils import Vector

def remove_over_xy_plane(target_object):
    """
    Removes the part of the target object that is above the XY plane.
    """
    # Get dimentions of the target.
    max_x = max([abs(v.co.x) for v in target_object.data.vertices]) + 1
    max_y = max([abs(v.co.y) for v in target_object.data.vertices]) + 1
    max_z = max([v.co.z for v in target_object.data.vertices]) + 1

    # Add cube that covers the part of the model that is above the XY plane.
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, max_z), scale=(max_x, max_y, max_z))
    boolean_cube = bpy.context.selected_objects[0]
    boolean_cube.name = 'boolean_cube'

    # Deselect all and set the active object to be the target again.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = target_object

    # Add a boolean modifier to the target object and set it to be the boolean cube.
    mod_bool = target_object.modifiers.new('Boolean', 'BOOLEAN')
    mod_bool.object = boolean_cube

    # Apply the modifier.
    print(str(target_object.modifiers[0].name))
    bpy.ops.object.modifier_apply(modifier=target_object.modifiers[0].name)

    # Delete the boolean cube.
    bpy.ops.object.select_all(action='DESELECT')
    boolean_cube.select_set(True)
    bpy.ops.object.delete()
    
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
             if f.normal.angle(up) < test_angle]
    
    print(faces)

    # Deselect everything.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    # Reselect the originally selected faces.
    bpy.ops.object.mode_set(mode='OBJECT')
    for face_idx in faces:
        print('selecting face', face_idx)
        target_object.data.polygons[face_idx].select = True
        
    # Delete selected faces.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # Reselect all.
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Change back to object mode.
    bpy.ops.object.mode_set(mode='OBJECT')

def thicken_shell(target_object, thickness):
    """
    Given a shell, extrudes it along the normals to thicken it.
    """
    bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":0.266901, "use_even_offset":False, "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "release_confirm":True, "use_accurate":False})


if __name__ == '__main__':
    # Save target object.
    target_object = bpy.context.active_object
    
    remove_over_xy_plane(target_object)
    convex_hull(target_object)
    delete_blocking_faces(target_object)
    thicken_shell(target_object, 1)