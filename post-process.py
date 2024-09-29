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

