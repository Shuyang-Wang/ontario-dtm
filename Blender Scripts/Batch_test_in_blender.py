import bpy
import os
import gc

# Disable global undo to save memory
bpy.context.preferences.edit.use_global_undo = False

def setup_scene():
    scene = bpy.context.scene
    # Set render engine to Cycles and use CPU rendering
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 5  # Reduce samples to lower values for speed

    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'NONE'  # Ensure CPU rendering
    
    # Set up Orthographic Camera
    cam_data = bpy.data.cameras.new("Orthographic_Camera")
    cam_data.type = 'ORTHO'
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, 0.0, 10.0)
    cam_data.ortho_scale = 1.0 
    scene.camera = cam_obj

    # Add Sun Light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 4.0
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)

def create_plane():
    # Create and return a new plane object
    bpy.ops.mesh.primitive_plane_add(size=1)  # Increase size to fill more of the camera view
    plane_obj = bpy.context.object
    plane_obj.name = "Plane"
    return plane_obj


def create_material(plane_obj, pseudocolor_path, displacement_path):
    mat = bpy.data.materials.new(name="PBR_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    # Base Color from pseudocolor texture
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex_color = nodes.new("ShaderNodeTexImage")
    tex_color.image = bpy.data.images.load(filepath=pseudocolor_path)
    # links.new(tex_color.outputs["Color"], bsdf.inputs["Base Color"])
    
    # Displacement from displacement texture
    tex_disp = nodes.new("ShaderNodeTexImage")
    tex_disp.image = bpy.data.images.load(filepath=displacement_path)
    disp_node = nodes.new("ShaderNodeDisplacement")
    disp_node.inputs["Scale"].default_value = 1.372
    links.new(tex_disp.outputs["Color"], disp_node.inputs["Height"])
    
    output_node = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])
    links.new(disp_node.outputs["Displacement"], output_node.inputs["Displacement"])

    plane_obj.data.materials.append(mat)

def render_image(output_path):
    scene = bpy.context.scene
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 2000
    scene.render.image_settings.file_format = 'TIFF'
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

def clean_up():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    for img in bpy.data.images:
        if img.users == 0:
            bpy.data.images.remove(img)
    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    gc.collect()

def process_folder(pseudocolor_folder, displacement_folder, output_folder):
    for pseudocolor_file in sorted(os.listdir(pseudocolor_folder))[:5]:
        if pseudocolor_file.endswith(".tif"):
            pseudocolor_path = os.path.join(pseudocolor_folder, pseudocolor_file)
            displacement_file = pseudocolor_file.replace("pseudocolor", "rescaled")
            displacement_path = os.path.join(displacement_folder, displacement_file)

            if os.path.exists(displacement_path):
                clean_up()
                plane = create_plane()
                create_material(plane, pseudocolor_path, displacement_path)

                output_file = pseudocolor_file.replace("pseudocolor", "shade")
                render_image(os.path.join(output_folder, output_file))
            else:
                print(f"Displacement map not found for {pseudocolor_file}")

# Define folder paths
workspace_folder = '/Volumes/WD Green/Data/DTM/Blender Topographic Map/W'
pseudocolor_folder = os.path.join(workspace_folder, "pseudocolor")
displacement_folder = os.path.join(workspace_folder, "DTM_adj")
output_folder = os.path.join(workspace_folder, "hillshade", "Original")

# Set up scene and process files
setup_scene()
process_folder(pseudocolor_folder, displacement_folder, output_folder)
