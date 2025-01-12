from pathlib import Path
import os

# Determine the absolute path to the shared folder
def find_repo_root(start_path):
    current_path = Path(start_path).resolve()
    while not (current_path / ".repo_root").exists():
        if current_path.parent == current_path:
            raise FileNotFoundError("Could not locate repo root marker (.repo_root)")
        current_path = current_path.parent
    return current_path

repo_root = find_repo_root(__file__)

# Ensure report directories and files exist
def folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# Ensure JSON files exist
def json_exists(json_path):
    if not os.path.exists(json_path):
        with open(json_path, "w") as file:
            file.write("{}")