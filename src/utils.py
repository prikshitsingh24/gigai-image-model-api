import subprocess
import os

def startComfyui(path:str):

    # Ensure the script is executable if needed
    os.chmod(path, 0o755)  # Optional, if the script isn't already executable

    # Run the Python script using subprocess
    command = f"python {path}"  # Or "python3" depending on the environment

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Print the output and error (if any)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Check if the script ran successfully
    if result.returncode == 0:
        print("Script executed successfully!")
    else:
        print(f"Script failed with return code {result.returncode}")