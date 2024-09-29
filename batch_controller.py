import os
import subprocess
import sys

# Paths
blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"  # Path to the Blender executable
script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script
script_path = os.path.join(script_dir ,"blender_batch_process.py")  # Path to the batch processing script

# Parameters
if len(sys.argv) > 1:
    workspace_folder = sys.argv[1]
else:
    raise ValueError("workspace_folder argument is required")

print(f"Workspace folder: {workspace_folder}")  # Debugging statement

pseudocolor_folder = os.path.join(workspace_folder, "pseudocolor")
batch_size = 100

# Count the total number of TIFF files
pseudocolor_files = [f for f in os.listdir(pseudocolor_folder) if f.endswith(".tif")]
total_files = len(pseudocolor_files)
total_batches = (total_files + batch_size - 1) // batch_size  # Calculate the total number of batches

print(f"Total files: {total_files}, Total batches: {total_batches}")  # Debugging statement

# Iterate over each batch and start a new Blender instance
for batch_number in range(total_batches):
    print(f"Processing batch {batch_number + 1} of {total_batches}")

    # Call Blender and pass the batch number, batch size, and workspace folder as arguments to the script
    result = subprocess.run([
        blender_path, "-b", "--python", script_path, 
        "--", "--batch_number", str(batch_number), "--batch_size", str(batch_size), "--workspace_folder", workspace_folder
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running Blender for batch {batch_number + 1}: {result.stderr}")
    else:
        print(f"Successfully processed batch {batch_number + 1}")
        print(result.stdout)  # Print the standard output for debugging

    print(f"Finished batch {batch_number + 1}")