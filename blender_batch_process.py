import bpy
import os
import gc
import json
import sys
import math

# Define paths (same as before)

# Accept batch number, batch size, and workspace folder from the command line
batch_number = int(sys.argv[sys.argv.index("--batch_number") + 1])
batch_size = int(sys.argv[sys.argv.index("--batch_size") + 1])
workspace_folder = sys.argv[sys.argv.index("--workspace_folder") + 1]

# Define folder paths
pseudocolor_folder = os.path.join(workspace_folder, "pseudocolor")
displacement_folder = os.path.join(workspace_folder, "DTM_adj")
output_folder = os.path.join(workspace_folder, "hillshade", "Original")

# Determine the path to the template .blend file relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(script_dir, "templete2.blend")

# Read the scale value from the JSON file
json_file_path = os.path.join(workspace_folder, "values.json")
with open(json_file_path, 'r') as json_file:
    scale = json.load(json_file)['scale']

# Load the template .blend file and disable global undo to save memory
bpy.ops.wm.open_mainfile(filepath=template_path)
bpy.context.preferences.edit.use_global_undo = False  # Disable global undo to save memory



def setup_lighting_and_camera():
    # Add Sun Light
    light = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
    light.data.energy = 2.0
    light.rotation_euler = (math.radians(45), 0.0, math.radians(100))
    bpy.context.collection.objects.link(light)

    # Set up an Orthographic Camera
    camera = bpy.data.objects.new("Orthographic_Camera", bpy.data.cameras.new("Orthographic_Camera"))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 1.0
    camera.location = (0.0, 0.0, 10.0)
    camera.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera

    print('Lighting and camera setup complete.')



def setup_render_settings(engine='CYCLES', use_gpu=False):
    scene = bpy.context.scene
    engine = engine.upper()

    if engine == 'CYCLES':
        scene.render.engine = 'CYCLES'
        cycles = scene.cycles
        cycles.samples = 1
        cycles.use_adaptive_sampling = True
        cycles.use_denoising = True
        cycles.device = 'GPU' if use_gpu else 'CPU'
        print(f'Render settings configured for Cycles with {"GPU" if use_gpu else "CPU"}.')

    elif engine == 'EEVEE':
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        eevee = scene.eevee
        eevee.taa_render_samples = 20
        eevee.use_gtao = True
        eevee.use_ssr = True
        eevee.use_soft_shadows = False
        print('Render settings configured for Eevee.')

    else:
        print('Invalid render engine specified. Choose either "CYCLES" or "EEVEE".')




def create_plane(tif_path, scale):
    # Create a new plane object
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))

    # Get the plane object
    plane_object = bpy.context.object
    plane_object.name = "Plane"

    # Apply the transform settings
    plane_object.scale = (1.0, 1.0, 1.0)
    plane_object.location = (0.0, 0.0, 0.0)
    plane_object.rotation_euler = (0.0, 0.0, 0.0)

    # Add a subdivision surface modifier
    subdivision_modifier = plane_object.modifiers.new(name='Subdivision', type='SUBSURF')
    subdivision_modifier.render_levels = 10
    subdivision_modifier.subdivision_type = 'SIMPLE'
    subdivision_modifier.use_creases = True
    subdivision_modifier.uv_smooth = 'PRESERVE_CORNERS'
    subdivision_modifier.boundary_smooth = 'ALL'

    # Add a displace modifier
    displace_modifier = plane_object.modifiers.new(name='Displace', type='DISPLACE')
    displace_modifier.strength = scale
    displace_modifier.mid_level = 1.0
    displace_modifier.texture_coords = 'UV'

    # Load the texture
    texture = bpy.data.textures.new(name="DisplaceTexture", type='IMAGE')
    texture.image = bpy.data.images.load(filepath=tif_path)
    texture.image.colorspace_settings.name = 'Non-Color'
    displace_modifier.texture = texture

    return plane_object


import bpy

def create_material(plane_object, pseudocolor_path, displacement_path, link_base_color=True):
    # Create new material with nodes
    material = bpy.data.materials.new(name="PBR_Material")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()

    # Add nodes
    bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    image_texture_node_1 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_2 = nodes.new(type="ShaderNodeTexImage")
    displacement_node = nodes.new(type="ShaderNodeDisplacement")

    # Set node properties
    bsdf_node.location, output_node.location = (0, 300), (400, 300)
    bsdf_node.inputs["Roughness"].default_value = 0.65
    image_texture_node_1.location, image_texture_node_2.location = (-300, 300), (-300, 0)
    image_texture_node_1.image = bpy.data.images.load(filepath=pseudocolor_path)
    image_texture_node_2.image = bpy.data.images.load(filepath=displacement_path)
    image_texture_node_2.image.colorspace_settings.name = 'Non-Color'
    displacement_node.location = (100, 0)
    displacement_node.inputs["Scale"].default_value = scale / 100
    displacement_node.inputs["Midlevel"].default_value = 200.0

    # Link nodes
    links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])
    if link_base_color:
        links.new(image_texture_node_1.outputs["Color"], bsdf_node.inputs["Base Color"])
    links.new(image_texture_node_2.outputs["Color"], displacement_node.inputs["Height"])
    links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])

    # Assign material to plane
    plane_object.data.materials.append(material)

    return material, image_texture_node_1.image, image_texture_node_2.image

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
    setup_render_settings(engine='EEVEE', use_gpu=True) 

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
                plane = create_plane(displacement_path, scale)
                create_material(plane, pseudocolor_path, displacement_path, link_base_color=False)  # Set up the material
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
