
import bpy
import os
import gc
import sys

# Define paths (same as before)

workspace_folder = '/Users/shuyang/Data/DTM/Halton/GTA-Halton-LidarDTM-C'
pseudocolor_folder = os.path.join(workspace_folder, "pseudocolor")
displacement_folder = os.path.join(workspace_folder, "DTM_adj")
output_folder = os.path.join(workspace_folder, "hillshade", "Original")
template_path = "/Users/shuyang/Documents/GitHub/ontario-dtm/Blender Scripts/templete2.blend"

# Accept batch number and batch size from the command line
batch_number = int(sys.argv[sys.argv.index("--batch_number") + 1])
batch_size = int(sys.argv[sys.argv.index("--batch_size") + 1])

# Load the template .blend file and disable global undo to save memory
bpy.ops.wm.open_mainfile(filepath=template_path)
bpy.context.preferences.edit.use_global_undo = False  # Disable global undo to save memory

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
    camera_data.ortho_scale = 1.0  # Set the desired orthographic scale
    camera_object = bpy.data.objects.new("Orthographic_Camera", camera_data)
    bpy.context.collection.objects.link(camera_object)

    # Set Camera location and orientation
    camera_object.location = (0.0, 0.0, 10.0)
    camera_object.rotation_euler = (0.0, 0.0, 0.0)

    # Set the camera as the active camera
    bpy.context.scene.camera = camera_object
    print('Lighting and camera setup complete.')

def setup_render_settings():
    scene = bpy.context.scene

    # Set the render engine to Eevee
    scene.render.engine = 'BLENDER_EEVEE_NEXT'

    # Eevee Settings
    eevee = scene.eevee
    eevee.taa_render_samples = 15
    eevee.use_gtao = True  # Enable Ambient Occlusion
    eevee.use_ssr = True    # Enable Screen Space Reflections

    # Ensure consistent lighting and shadows
    eevee.use_soft_shadows = False  # Disable soft shadows for consistency

    print('Render settings configured for Eevee.')

def create_plane():
    # Create a new plane object
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))

    # Get the plane object
    plane_object = bpy.context.object
    plane_object.name = "Plane"

    # Apply the transform settings
    plane_object.scale = (1.0, 1.0, 1.0)
    plane_object.location = (0.0, 0.0, 0.0)
    plane_object.rotation_euler = (0.0, 0.0, 0.0)

    return plane_object

def create_material(plane_object, pseudocolor_path, displacement_path):
    # Create new material
    material = bpy.data.materials.new(name="PBR_Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Clear all nodes
    nodes.clear()

    # Add Principled BSDF node
    bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf_node.location = (0, 300)
    bsdf_node.inputs["Metallic"].default_value = 0.0
    bsdf_node.inputs["Roughness"].default_value = 0.65
    bsdf_node.inputs["IOR"].default_value = 1.5
    bsdf_node.inputs["Alpha"].default_value = 1.0

    # Add Material Output node
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 300)

    # Link BSDF to Material Output
    links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

    # Add Image Texture node for Base Color
    image_texture_node_1 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_1.location = (-300, 300)
    pseudocolor_image = bpy.data.images.load(filepath=pseudocolor_path)
    image_texture_node_1.image = pseudocolor_image
    image_texture_node_1.extension = 'EXTEND'
    image_texture_node_1.interpolation = 'Cubic'  

    # Link Image Texture to Principled BSDF Base Color
    links.new(image_texture_node_1.outputs["Color"], bsdf_node.inputs["Base Color"])

    # Add Image Texture node for Displacement
    image_texture_node_2 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_2.location = (-300, 0)
    displacement_image = bpy.data.images.load(filepath=displacement_path)
    image_texture_node_2.image = displacement_image
    image_texture_node_2.extension = 'EXTEND'
    image_texture_node_2.image.colorspace_settings.name = 'Non-Color'
    image_texture_node_2.interpolation = 'Cubic' 
    
    # Add Displacement node
    displacement_node = nodes.new(type="ShaderNodeDisplacement")
    displacement_node.location = (100, 0)
    displacement_node.inputs["Scale"].default_value = 1.548
    displacement_node.inputs["Midlevel"].default_value = 200.0

    # Link Image Texture to Displacement Height
    links.new(image_texture_node_2.outputs["Color"], displacement_node.inputs["Height"])

    # Link Displacement node to Material Output Displacement
    links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])

    # Assign the material to the plane
    plane_object.data.materials.append(material)

    return material, pseudocolor_image, displacement_image

def render_orthophoto(output_path):
    bpy.context.scene.render.resolution_x = 2000
    bpy.context.scene.render.resolution_y = 2000
    bpy.context.scene.render.resolution_percentage = 100

    bpy.context.scene.render.image_settings.file_format = 'TIFF'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    bpy.context.scene.render.image_settings.color_depth = '8'
    bpy.context.scene.render.image_settings.compression = 1

    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

def remove_existing_objects():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh_data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)
    
    for img in bpy.data.images:
        if img.users == 0:
            bpy.data.images.remove(img)

    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)

    gc.collect()


def process_batch(files, batch_number, override_output_file=False):
    setup_lighting_and_camera()
    setup_render_settings()

    for pseudocolor_file in files:
        if pseudocolor_file.endswith(".tif"):
            pseudocolor_path = os.path.join(pseudocolor_folder, pseudocolor_file)
            displacement_file = pseudocolor_file.replace("pseudocolor", "rescaled")
            displacement_path = os.path.join(displacement_folder, displacement_file)

            # Set the output file path
            output_file = pseudocolor_file.replace("pseudocolor", "shade")
            output_path = os.path.join(output_folder, output_file)

            # Check if output file already exists and whether to override it
            if os.path.exists(output_path) and not override_output_file:
                print(f"Output file already exists: {output_file}. Skipping.")
                continue  # Skip to the next file without doing any Blender operations

            # Only proceed with Blender operations if the output file doesn't exist or override is True
            if os.path.exists(displacement_path):
                remove_existing_objects()  # Clean up any previous objects
                plane = create_plane()  # Create a new plane
                create_material(plane, pseudocolor_path, displacement_path)  # Set up the material
                render_orthophoto(output_path)  # Render the output to the file
            else:
                print(f"Displacement map not found for {pseudocolor_file}")

    gc.collect()



def process_folder_in_batches(batch_number, batch_size):
    pseudocolor_files = sorted([f for f in os.listdir(pseudocolor_folder) if f.endswith(".tif")])
    
    start_idx = batch_number * batch_size
    end_idx = min(start_idx + batch_size, len(pseudocolor_files))
    batch_files = pseudocolor_files[start_idx:end_idx]
    
    process_batch(batch_files, batch_number)

process_folder_in_batches(batch_number, batch_size)
