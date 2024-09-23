import bpy
import os
import gc

template_path = "/Users/shuyang/Documents/GitHub/ontario-dtm/Blender Scripts/template.blend"
bpy.ops.wm.open_mainfile(filepath=template_path)
# Disable global undo to save memory
bpy.context.preferences.edit.use_global_undo = False

def setup_color_management():
    scene = bpy.context.scene
    scene.view_settings.view_transform = 'Standard'  # Options: 'Filmic', 'Standard', etc.
    scene.view_settings.look = 'None'  # Adjust as needed
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    print('Color management settings configured')

#setup_color_management()


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
    print('setup lighting and camera')


setup_lighting_and_camera()


def setup_render_settings():
    scene = bpy.context.scene

    # Set the render engine to Eevee
    scene.render.engine = 'BLENDER_EEVEE_NEXT'

    # Eevee Settings
    eevee = scene.eevee
    eevee.taa_render_samples = 15
    eevee.use_gtao = True  # Enable Ambient Occlusion
    eevee.use_ssr = True    # Enable Screen Space Reflections
    #eevee.shadow_method = 'ESM'  # Example shadow method

    # Ensure consistent lighting and shadows
    eevee.use_soft_shadows = False  # Disable soft shadows for consistency

    print('Render settings configured for Eevee with specified parameters')


setup_render_settings()


def create_plane():
    # Create a new plane object
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))

    # Get the plane object
    plane_object = bpy.context.object
    plane_object.name = "Plane"

    # Apply the transform settings
    plane_object.scale = (1.0, 1.0, 1.0)  # Set scale to (1, 1, 0.001)
    plane_object.location = (0.0, 0.0, 0.0)  # Set location to (0, 0, 0)
    plane_object.rotation_euler = (0.0, 0.0, 0.0)  # Set rotation to (0, 0, 0)

    print ('create plane')

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

    print ('set base color')

    # Add Image Texture node for Base Color
    image_texture_node_1 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_1.location = (-300, 300)
    pseudocolor_image = bpy.data.images.load(filepath=pseudocolor_path)
    image_texture_node_1.image = pseudocolor_image
    image_texture_node_1.extension = 'EXTEND'  # Prevent texture from repeating
    image_texture_node_1.interpolation = 'Cubic'  

    # Link Image Texture to Principled BSDF Base Color
    links.new(image_texture_node_1.outputs["Color"], bsdf_node.inputs["Base Color"])

    # Add Image Texture node for Displacement
    image_texture_node_2 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_2.location = (-300, 0)
    displacement_image = bpy.data.images.load(filepath=displacement_path)
    image_texture_node_2.image = displacement_image
    image_texture_node_2.extension = 'EXTEND'
    image_texture_node_2.image.colorspace_settings.name = 'Non-Color'  # Non-color data for displacement
    image_texture_node_2.interpolation = 'Cubic' 
    
    # Add Displacement node
    displacement_node = nodes.new(type="ShaderNodeDisplacement")
    displacement_node.location = (100, 0)
    displacement_node.inputs["Scale"].default_value = 0.491 #0.6
    displacement_node.inputs["Midlevel"].default_value = 200.0

    # Link Image Texture to Displacement Height
    links.new(image_texture_node_2.outputs["Color"], displacement_node.inputs["Height"])

    # Link Displacement node to Material Output Displacement
    links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])

    # Assign the material to the plane
    plane_object.data.materials.append(material)  # Create a new material slot and assign

    print('create material')

    return material, pseudocolor_image, displacement_image

def render_orthophoto(output_path):
    # Set up Render Settings
    bpy.context.scene.render.resolution_x = 2000  # Resolution X
    bpy.context.scene.render.resolution_y = 2000  # Resolution Y
    bpy.context.scene.render.resolution_percentage = 100  # 100% of the resolution

    # Set output file format and other options
    bpy.context.scene.render.image_settings.file_format = 'TIFF'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Color format RGBA
    bpy.context.scene.render.image_settings.color_depth = '8'  # Color depth 8-bit
    bpy.context.scene.render.image_settings.compression = 1  # TIFF compression: Deflate

    # Set output path for the rendered image
    bpy.context.scene.render.filepath = output_path

    # Render the orthophoto
    bpy.ops.render.render(write_still=True)


def remove_existing_objects():
    # Function to remove all existing objects, images, and materials from the previous iteration
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh_data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)
    
    # Remove all images (ensuring no dangling references)
    for img in bpy.data.images:
        if img.users == 0:
            bpy.data.images.remove(img)

    # Remove all materials (ensuring no dangling references)
    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)

    # Force garbage collection to clear memory
    gc.collect()

def process_folder(pseudocolor_folder, displacement_folder, output_folder):
    # Iterate through all files in the pseudocolor folder
    n = 0
    for pseudocolor_file in sorted(os.listdir(pseudocolor_folder)):
        n += 1
        if n > 5000:
            break
        if pseudocolor_file.endswith(".tif"):  # Ensure the file is a TIFF image
            print ("f")
            pseudocolor_path = os.path.join(pseudocolor_folder, pseudocolor_file)

            # Derive the displacement path (assuming matching filenames for displacement)
            displacement_file = pseudocolor_file.replace("DTM", "DTM")
            displacement_path = os.path.join(displacement_folder, displacement_file)

            if os.path.exists(displacement_path):
                # Clean up objects from the previous iteration before creating new ones
                remove_existing_objects()

                # Create a new plane for each iteration
                plane = create_plane()

                # Create the material using the current pseudocolor and displacement paths
                material, pseudocolor_image, displacement_image = create_material(plane, pseudocolor_path, displacement_path)

                # Derive the output path for the render
                output_file = pseudocolor_file.replace("DTM", "shade")
                output_path = os.path.join(output_folder, output_file)

                # Render the orthophoto
                render_orthophoto(output_path)
                

            else:
                print(f"Displacement map not found for {pseudocolor_file}")

    # Final cleanup of remaining objects, images, and materials after the loop
    # remove_existing_objects()
    



# Define folders
# pseudocolor_folder = "/Volumes/WD Green/Data/DTM/Blender Topographic Map/W/pseudocolor"
# displacement_folder = "/Volumes/WD Green/Data/DTM/Blender Topographic Map/W/DTM_adj"
# output_folder = "/Volumes/WD Green/Data/DTM/Blender Topographic Map/W/hillshade"


import os

# Define workspace folder
workspace_folder = "/Users/shuyang/Data/DTM/LakeNipissing-DTM-D" 

# Define specific subfolders based on the workspace
pseudocolor_folder = os.path.join(workspace_folder, "pseudocolor")  # Folder for pseudocolor images
displacement_folder = os.path.join(workspace_folder, "DTM_adj")  # Folder for adjusted DTM displacement files
output_folder = os.path.join(workspace_folder, "hillshade","Original")  # Folder for hillshade output

# Process all pseudocolor files
process_folder(pseudocolor_folder, displacement_folder, output_folder)