import subprocess

def run_script(script_path, *args):
    result = subprocess.run(['python', script_path, *args], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_path}: {result.stderr}")
    else:
        print(f"Successfully ran {script_path}")
        print(result.stdout)  # Print the standard output for debugging

# Paths to the scripts
pre_process_script = 'pre-process.py'
batch_controller_script = 'batch_controller.py'
post_process_script = 'post-process.py'

# Workspace folder
workspace_folder = '/Volumes/WD Green/Data/DTM/Test-W'

# Run pre-process.py
print("Running pre-process.py...")
run_script(pre_process_script, workspace_folder)

# Run batch_controller.py
print("Running batch_controller.py...")
run_script(batch_controller_script, workspace_folder)

# Run post-process.py
print("Running post-process.py...")
run_script(post_process_script, workspace_folder)

print("Workflow completed.")