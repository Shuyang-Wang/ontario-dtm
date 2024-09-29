import os
import bpy

def remove_existing_objects():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh_data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)

def create_plane():
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    return bpy.context.object

def create_material(plane_object, pseudocolor_path, displacement_path):
    material = bpy.data.materials.new(name="Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    bsdf_node = nodes.get("Principled BSDF")
    output_node = nodes.get("Material Output")

    image_texture_node_1 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_1.location = (-300, 300)
    pseudocolor_image = bpy.data.images.load(filepath=pseudocolor_path)
    image_texture_node_1.image = pseudocolor_image
    image_texture_node_1.extension = 'EXTEND'
    image_texture_node_1.interpolation = 'Cubic'
    links.new(image_texture_node_1.outputs["Color"], bsdf_node.inputs["Base Color"])

    image_texture_node_2 = nodes.new(type="ShaderNodeTexImage")
    image_texture_node_2.location = (-300, 0)
    displacement_image = bpy.data.images.load(filepath=displacement_path)
    image_texture_node_2.image = displacement_image
    image_texture_node_2.extension = 'EXTEND'
    image_texture_node_2.image.colorspace_settings.name = 'Non-Color'
    image_texture_node_2.interpolation = 'Cubic'
    
    displacement_node = nodes.new(type="ShaderNodeDisplacement")
    displacement_node.location = (100, 0)
    displacement_node.inputs["Scale"].default_value = 1.372
    displacement_node.inputs["Midlevel"].default_value = 200.0
    links.new(image_texture_node_2.outputs["Color"], displacement_node.inputs["Height"])
    links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])

    plane_object.data.materials.append(material)
    return material, pseudocolor_image, displacement_image

def render_orthophoto(output_path):
    scene = bpy.context.scene
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 2000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'TIFF'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 1
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

def process_files(pseudocolor_folder, displacement_folder, output_folder):
    for n, pseudocolor_file in enumerate(os.listdir(pseudocolor_folder), start=1):
        if n > 5000:
            break
        if pseudocolor_file.endswith(".tif"):
            pseudocolor_path = os.path.join(pseudocolor_folder, pseudocolor_file)
            displacement_file = pseudocolor_file.replace("pseudocolor", "rescaled")
            displacement_path = os.path.join(displacement_folder, displacement_file)

            if os.path.exists(displacement_path):
                remove_existing_objects()
                plane = create_plane()
                create_material(plane, pseudocolor_path, displacement_path)
                output_file = pseudocolor_file.replace("pseudocolor", "shade")
                render_orthophoto(os.path.join(output_folder, output_file))
            else:
                print(f"Displacement map not found for {pseudocolor_file}")

workspace_folder = '/Users/shuyang/Data/DTM/Lake Erie/LIDAR2016to18_DTM-LkErie-R'
process_files(
    os.path.join(workspace_folder, "pseudocolor"),
    os.path.join(workspace_folder, "DTM_adj"),
    os.path.join(workspace_folder, "hillshade", "Original")
)