import os
import subprocess

# Paths
blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"  # Path to the Blender executable
script_path = "/Users/shuyang/Documents/GitHub/ontario-dtm/Blender Scripts/blender_batch_process.py"  # Path to the batch processing script

# Parameters
workspace_folder = '/Users/shuyang/Data/DTM/Lake Erie/LIDAR2016to18_DTM-LkErie-R'
pseudocolor_folder = os.path.join(workspace_folder, "pseudocolor")
batch_size = 100

# Count the total number of TIFF files
pseudocolor_files = [f for f in os.listdir(pseudocolor_folder) if f.endswith(".tif")]
total_files = len(pseudocolor_files)
total_batches = (total_files + batch_size - 1) // batch_size  # Calculate the total number of batches

# Iterate over each batch and start a new Blender instance
for batch_number in range(total_batches):
    print(f"Processing batch {batch_number + 1} of {total_batches}")

    # Call Blender and pass the batch number and batch size as arguments to the script
    subprocess.run([
        blender_path, "-b", "--python", script_path, 
        "--", "--batch_number", str(batch_number), "--batch_size", str(batch_size)
    ])

    print(f"Finished batch {batch_number + 1}")
