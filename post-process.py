# %%
from osgeo import gdal, osr
import os

# %%
# Define workspace folder
import sys
import os

workspace_folder = sys.argv[1]
# Use workspace_folder in your script

# Define specific subfolders based on the workspace
input_folder = os.path.join(workspace_folder, "hillshade","Original")  #· Input folder for hillshade data
output_folder = os.path.join(workspace_folder, "hillshade", "Projected")  # Output folder for projected hillshade data

# %%


# %%
import os
from osgeo import gdal, osr



# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function to project a single file
def project_file(input_file, output_file):
    # Open the input TIFF file
    dataset = gdal.Open(input_file)

    if dataset is None:
        print(f"Error opening {input_file}")
        return

    # Set up geotransformation parameters based on filename (modify as per your logic)
    origin_x = float(input_file.split('/')[-1][5:9] + '00')  # Replace with the correct value from the image
    origin_y = float(input_file.split('/')[-1][9:14] + '00') + 1000  # Replace with the correct value from the image

    # Pixel size
    pixel_width = 0.5
    pixel_height = -0.5  # Negative for georeferenced rasters (top-to-bottom)

    # Define the geotransform (this defines where the image fits in the real world)
    geotransform = (origin_x, pixel_width, 0, origin_y, 0, pixel_height)

    # Create a new GeoTIFF with georeferencing
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.CreateCopy(output_file, dataset, 0)

    # Apply the geotransformation to the dataset
    out_dataset.SetGeoTransform(geotransform)

    # Set the coordinate system (assumed to be EPSG:26917 for UTM Zone 17N, adjust if necessary)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(26917)  # Replace with the appropriate EPSG code if needed
    out_dataset.SetProjection(srs.ExportToWkt())

    # Flush data to disk and close the dataset
    out_dataset.FlushCache()
    out_dataset = None
    dataset = None

    print(f"GeoTIFF saved to {output_file}")

# Iterate over files in the input folder (no subfolders)
for filename in sorted(os.listdir(input_folder)):
    if filename.endswith(".tif"):  # Process only .tif files
        input_file = os.path.join(input_folder, filename)
        output_file = os.path.join(output_folder, filename.replace('.tif', '.tif'))
        project_file(input_file, output_file)

# After processing all files, merge the output GeoTIFFs into one file
# Collect all output files
output_files = [os.path.join(output_folder, filename.replace('.tif', '.tif'))
                for filename in os.listdir(input_folder)
                if filename.endswith('.tif')]

# %%


# %%
# Define the name of the VRT and GeoTIFF output files
vrt_output_file = os.path.join(output_folder, 'merged_output.vrt')
tif_output_file = os.path.join(output_folder, 'merged_output.tif')
gdal.BuildVRT(vrt_output_file, output_files)
print("Converting the virtual mosaic to GeoTIFF using gdal_translate...")
gdal.Translate(tif_output_file, vrt_output_file, format='GTiff')

# %%


# %% [markdown]
# - optimized

# %% [markdown]
# # TIFF with JPEG copression

# %% [markdown]
# ## GDAL

# %%
import os
from osgeo import gdal

merged_output_file = os.path.join(output_folder, 'merged_output.tif')  # Path to your merged GeoTIFF file
optimized_output_file = os.path.join(output_folder, 'merged_output_o_gdal_10.tif')  # Output file path for the optimized version

def convert_to_jpeg_compressed_geotiff_with_gdal(input_file, output_file, scale_factor=0.5, quality=60):
    # Open the source dataset
    dataset = gdal.Open(input_file)

    # Get the original dimensions
    original_width = dataset.RasterXSize
    original_height = dataset.RasterYSize

    # Calculate the new dimensions
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)

    # Define options for GDAL Translate to downsize, compress, and tile the output
    gdal_translate_options = gdal.TranslateOptions(
        width=new_width,
        height=new_height,
        creationOptions=[
            'COMPRESS=JPEG',        # Apply JPEG compression
            f'JPEG_QUALITY={quality}',  # Set the JPEG quality
            'TILED=YES',            # Enable tiling
            'BLOCKXSIZE=256',        # Tile width
            'BLOCKYSIZE=256',        # Tile height
        
        ]
    )

    # Use GDAL Translate to create the downsized, compressed, and tiled output file
    gdal.Translate(output_file, dataset, options=gdal_translate_options)

    print(f"Converted, downsized, and saved image to {output_file} with JPEG compression, tiling, and original bands.")

# Using the defined variables, downsizing to 50% of the original resolution
convert_to_jpeg_compressed_geotiff_with_gdal(merged_output_file, optimized_output_file, scale_factor=1, quality=30)


# %%


# %%


# %% [markdown]
# # COG

# %%
import os
from osgeo import gdal

def generate_cog_with_jpeg(input_file, output_file):
    """
    Generates a Cloud Optimized GeoTIFF (COG) from the input GeoTIFF file with JPEG compression and specified quality.
    
    Parameters:
    - input_file: Path to the input GeoTIFF file.
    - output_file: Path where the COG will be saved.
    """
    
    # Open the input GeoTIFF file
    dataset = gdal.Open(input_file)
    
    # Step 1: Generate overviews if needed (using cubic resampling)
    print("Generating overviews...")
    dataset.BuildOverviews("CUBIC", [2, 4, 8, 16])  # Generate overviews with downsampling factors

    # Step 2: Define options for generating a Cloud Optimized GeoTIFF with JPEG compression and quality of 60
    cog_options = gdal.TranslateOptions(
        format='COG',  # Output format as Cloud Optimized GeoTIFF
        creationOptions=[
            'COMPRESS=JPEG',  # Use JPEG compression
            'QUALITY=60',  # Set JPEG quality to 60
            'BIGTIFF=IF_NEEDED'  # Enable BigTIFF if the file exceeds 4GB
        ]
    )
    # Step 3: Translate the dataset to a COG
    print(f"Generating Cloud Optimized GeoTIFF for {input_file} with JPEG compression (quality=60)...")

    gdal.Translate(output_file, dataset, options=cog_options)

    print(f"COG saved to: {output_file}")

# Example usage:
input_file = os.path.join(output_folder, 'merged_output.tif')  # Replace with actual input file path
output_file = os.path.join(output_folder, 'merged_output_cog.tif')  # Replace with actual output file path
generate_cog_with_jpeg(input_file, output_file)

# %%


# %% [markdown]
# # KMZ

# %%
import os
from osgeo import gdal
import zipfile
import xml.etree.ElementTree as ET

# Function to convert individual GeoTIFF raster files to KML super overlay
def convert_raster_to_kml(input_raster, output_kml_folder):
    # Register all available GDAL drivers
    gdal.AllRegister()

    # Open the input raster file
    raster = gdal.Open(input_raster)
    if raster is None:
        print(f"Failed to open file: {input_raster}")
        return

    # Ensure the raster has a spatial reference and is georeferenced
    if raster.GetProjection() == '':
        print(f"The input raster {input_raster} is not georeferenced.")
        return

    # Define the driver for KML super overlay output
    driver = gdal.GetDriverByName('KMLSUPEROVERLAY')
    if driver is None:
        print("KMLSUPEROVERLAY driver not found")
        return

    try:
        # Create the folder for the KML output
        tile_name = os.path.basename(input_raster).replace('.tif', '')
        tile_output_folder = os.path.join(output_kml_folder, tile_name)

        if not os.path.exists(tile_output_folder):
            os.makedirs(tile_output_folder)

        # Define the output KML path (it will generate both KML and image tiles in the folder)
        output_tile_kml = os.path.join(tile_output_folder, f"{tile_name}.kml")

        # Write the KML super overlay to a folder (this also creates associated images)
        driver.CreateCopy(output_tile_kml, raster)
        print(f"Tile {tile_name} converted successfully to KML and images: {output_tile_kml}")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Close the dataset
        raster = None

# Function to create a master KML file that references all individual KML files
def create_master_kml(kml_folder, master_kml_path):
    kml_namespace = "http://www.opengis.net/kml/2.2"
    ET.register_namespace("", kml_namespace)

    # Create the root KML element
    kml = ET.Element("{%s}kml" % kml_namespace)
    document = ET.SubElement(kml, "Document")

    # Loop through each subfolder (each tile)
    for tile_name in os.listdir(kml_folder):
        tile_folder = os.path.join(kml_folder, tile_name)
        if os.path.isdir(tile_folder):
            tile_kml_file = os.path.join(tile_folder, f"{tile_name}.kml")
            if os.path.exists(tile_kml_file):
                # Create a NetworkLink to the tile KML file
                network_link = ET.SubElement(document, "NetworkLink")
                name = ET.SubElement(network_link, "name")
                name.text = tile_name
                link = ET.SubElement(network_link, "Link")
                href = ET.SubElement(link, "href")
                href.text = f"{tile_name}/{tile_name}.kml"  # Relative path inside the KMZ
                view_refresh_mode = ET.SubElement(link, "viewRefreshMode")
                view_refresh_mode.text = "onRegion"
    
    # Write the master KML to a file
    tree = ET.ElementTree(kml)
    tree.write(master_kml_path, encoding="UTF-8", xml_declaration=True)
    print(f"Master KML file created: {master_kml_path}")

# Function to zip all KML files and associated images into a single KMZ
def create_kmz(kml_folder, kmz_file, master_kml_path):
    with zipfile.ZipFile(kmz_file, 'w', zipfile.ZIP_DEFLATED) as kmz:
        # Add the master KML file as 'doc.kml' at the root
        kmz.write(master_kml_path, 'doc.kml')

        # Loop through each subfolder inside the KML folder
        for root, _, files in os.walk(kml_folder):
            for file in files:
                file_path = os.path.join(root, file)
                # Exclude the master KML file (already added as 'doc.kml')
                if file_path == master_kml_path:
                    continue
                # Calculate the relative path inside the KMZ
                relative_path = os.path.relpath(file_path, kml_folder)
                kmz.write(file_path, relative_path)
    print(f"Master KMZ file created successfully: {kmz_file}")

# Define the input and output folder paths
input_folder = '/Users/shuyang/Data/DTM/LakeNipissing-DTM-A/hillshade/Projected/'  # Folder with the individual projected GeoTIFF tiles
output_kml_folder = '/Users/shuyang/Data/DTM/LakeNipissing-DTM-A/hillshade/Projected/KML_tiles/'  # Folder to store individual KML files and image tiles

# Ensure the output folder for KML files exists
if not os.path.exists(output_kml_folder):
    os.makedirs(output_kml_folder)

# Iterate over the individual GeoTIFF tiles and convert each to KML
for filename in os.listdir(input_folder):
    if filename.endswith("_shade.tif"):  # Process only the projected .tif files
        input_raster = os.path.join(input_folder, filename)
        print(f"Converting {filename} to KML...")
        convert_raster_to_kml(input_raster, output_kml_folder)

# Define the path for the master KML file
master_kml_path = os.path.join(output_kml_folder, 'master.kml')

# Create the master KML file that references all individual KML files
create_master_kml(output_kml_folder, master_kml_path)

# Define the final KMZ output file path
kmz_file = os.path.join(output_kml_folder, 'merged_output.kmz')

# Create the final KMZ by zipping the master KML and supporting files
create_kmz(output_kml_folder, kmz_file, master_kml_path)



# %%


# %%


# %%



