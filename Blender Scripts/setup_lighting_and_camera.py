import bpy

def setup_lighting_and_camera():
    # Add Sun Light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 2.0
    light_object = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.collection.objects.link(light_object)

    # Set Sun light angle (default rotation)
    light_object.rotation_euler = (0.0, 0.0, 0.0)

    # Set up an Orthographic Camera
    camera_data = bpy.data.cameras.new(name="Orthographic_Camera")
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 2.0  # Set the desired orthographic scale
    camera_object = bpy.data.objects.new("Orthographic_Camera", camera_data)
    bpy.context.collection.objects.link(camera_object)

    # Set Camera location and orientation
    camera_object.location = (0.0, 0.0, 10.0)
    camera_object.rotation_euler = (0.0, 0.0, 0.0)

    # Set the camera as the active camera
    bpy.context.scene.camera = camera_object


setup_lighting_and_camera()