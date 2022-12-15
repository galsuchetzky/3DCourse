import bpy
#import bmesh

from math import radians
from mathutils import Vector

def copy(target_object):
    """
    Copy the active object in place.
    """
    bpy.ops.object.duplicate(linked=False)
    return bpy.context.active_object
    

def remove_over_xy_plane(target_object, z_offset):
    """
    Removes the part of the target object that is above the XY plane.
    :param z_offset: the z value of the height to remove above.
    """
    # Get dimentions of the target. +10 to make sure that the cube is bigger than the object.
    max_x = max([abs((target_object.matrix_world @ v.co).x) for v in target_object.data.vertices]) + 10
    max_y = max([abs((target_object.matrix_world @ v.co).y) for v in target_object.data.vertices]) + 10
    max_z = max([(target_object.matrix_world @ v.co).z for v in target_object.data.vertices]) + 10

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
    
def add_attach_port(target_object, z_offset):
    """
    Adds an attach port location to the model.
    Should be used before the convex hull operation.
    """
    # Get max x to know where to put the port. + 1 to be a bit further.
    port_x = max([(target_object.matrix_world @ v.co).x for v in target_object.data.vertices]) + 1
    
    # Calculate the height of the port.
    port_height = abs(min([(target_object.matrix_world @ v.co).z for v in target_object.data.vertices])) / 4

    # Calculate the port width.
    port_width = (max([(target_object.matrix_world @ v.co).y for v in target_object.data.vertices]) - min([(target_object.matrix_world @ v.co).y for v in target_object.data.vertices])) / 4
    
    # Calculate the port y.
    port_y = (max([(target_object.matrix_world @ v.co).y for v in target_object.data.vertices]) + min([(target_object.matrix_world @ v.co).y for v in target_object.data.vertices])) / 2
    
    # Add port cube.
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(port_x, port_y, z_offset - port_height/2), scale=(1, port_width, port_height))
    port_cube = bpy.context.selected_objects[0]
    port_cube.name = 'port_cube'
    
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
    
def get_inner_vertices(target_object):
    """
    Iterate over all faces and collect the vertices that are attached to faces with normals that point up.
    """
    # Deselect all vertices.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get all vertices that are attached to a polygon with normal that points up.
    vertices = []
    for f in target_object.data.polygons:            
        for v in f.vertices:
            up = Vector((0, 0, 1))
            test_angle = radians(90)
            if f.normal.angle(up) < test_angle:
                vertices.append(v)
                target_object.data.vertices[v].select = True
            
    return vertices
    
    
def is_inside(p, max_dist, obj):
    # max_dist = 1.84467e+19
    print('resp=', obj.closest_point_on_mesh(p, distance=max_dist))
    result, point, normal, face = obj.closest_point_on_mesh(p, distance=max_dist)
    
    # Face not found.
    if not result:
        return False
    
    # Face found, check if inside.
    p2 = point-p
    v = p2.dot(normal)
    print(v)
    return not(v < 0.0)

def raise_vertices(target_object, limit_object, vertices):
    """
    For each vertex of the target_object in the vertices list, raise it up by small steps until it reaches 0 or collides with the limit object.
    If collided, leave it at the last non-colliding location.
    If reached 0, return it to it's place (maybe leave it at 0?)
    try this resource: https://blender.stackexchange.com/questions/31693/how-to-find-if-a-point-is-inside-a-mesh
    """
    for v in vertices:
        cur_vertex = target_object.data.vertices[vertices[v]]
        cur_vertex.select = True
        pos_world = target_object.matrix_world @ cur_vertex.co
        
        while not is_inside(cur_vertex.co, 0.1, limit_object) and pos_world.z < 0:
            pos_world = target_object.matrix_world @ cur_vertex.co
            pos_world.z += 0.05
            cur_vertex.co = target_object.matrix_world.inverted() @ pos_world

def get_attach_port_vertices(target_object, type):
    """
    Selects the port vertices and returns them.
    use type to specify hanger or holder with HANGER, HOLDER.
    """
    
    # Deselect all vertices.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the 4 vertices. Note that if we calculate for the  hanger we don't want to reverse.
    vertices = sorted(target_object.data.vertices, reverse=type=='HOLDER', key=lambda v: (target_object.matrix_world @ v.co).x)[:4]
    
    print(vertices)
    for v in vertices:
        v.select = True
        
    return vertices

def import_hanger(type):
    """
    imports the requested hanger.
    TABLE for table mount.
    WALL for wall mount.
    CYLINDER for cylinder mount.
    """
    wall_mount_filepath = r"E:\Projects\3DCourse\files\mounts\wall_mount.stl"
    bpy.ops.import_mesh.stl(filepath=wall_mount_filepath)
    hanger = bpy.context.active_object
    
    return hanger

def connect_holder_hanger(holder, hanger):
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






def main():
    """
    Runs the logic of the program.
    """
    z_offset=0
    wall_thickness = 10
    
    # Save target object.
    limit_object = bpy.context.active_object
    
    # Copy the target object.
    holder = copy(limit_object)
    
    # Remove a part from the top, where we dont want the holder to form.
    remove_over_xy_plane(holder, z_offset)
    
    # boolean a connection port to the object.
    add_attach_port(holder, z_offset)
    
    # Calculate the convex hull.
    convex_hull(holder)
    
    # Remove all faces that restrict the object from being pulled straight up.
    delete_blocking_faces(holder)
    
    # Scale the shell a bit.
    uniform_scale(holder, 1.05)
    
    # Thicken the shell to create walls.
    thicken_shell(holder, wall_thickness)
    
    # Get the attach port vertices.
    port_vertices = get_attach_port_vertices(holder, 'HOLDER')
    
    # Import the hanger of the specified type.
    hanger = import_hanger('WALL')
    
    # Get the attach port vertices.
    port_vertices = get_attach_port_vertices(hanger, 'HANGER')
    
    # Connect the holder and the hanger with a connecting arm.
    connect_holder_hanger(holder, hanger)
    
def test():
    """
    for testing code.
    """
    z_offset=0
    wall_thickness = 10
    
    # Save target object.
    limit_object = bpy.context.active_object
    
    # Copy the target object.
    holder = copy(limit_object)
    
    # Remove a part from the top, where we dont want the holder to form.
    remove_over_xy_plane(holder, z_offset)
    
    # boolean a connection port to the object.
    add_attach_port(holder, z_offset)
    
    # Calculate the convex hull.
    convex_hull(holder)
    
    # Remove all faces that restrict the object from being pulled straight up.
    delete_blocking_faces(holder)
    
    # Scale the shell a bit.
    uniform_scale(holder, 1.05)
    
    # Thicken the shell to create walls.
    thicken_shell(holder, wall_thickness)
    
    # Get the attach port vertices.
    port_vertices = get_attach_port_vertices(holder, 'HOLDER')
    
    # Import the hanger of the specified type.
    hanger = import_hanger('WALL')
    
    # Get the attach port vertices.
    port_vertices = get_attach_port_vertices(hanger, 'HANGER')
    
    # Connect the holder and the hanger with a connecting arm.
    connect_holder_hanger(holder, hanger)
    
if __name__ == '__main__':
    main()
#    test()
    
#    apply_subsurf_modifier(target_object)
#    vertices = get_inner_vertices(target_object)
#    print(len(vertices))
#    raise_vertices(target_object, limit_object, vertices)
    
    