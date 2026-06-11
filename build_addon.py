import os
import zipfile
import shutil

def create_addon_zip():
    addon_dir = "render_analyzer"
    output_zip = "render_analyzer_addon.zip"
    
    print(f"Creating {output_zip} from {addon_dir}/ ...")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(addon_dir):
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            for file in files:
                if file.endswith(".pyc") or file.endswith(".pyo"):
                    continue
                file_path = os.path.join(root, file)
                # Ensure the zip structure starts with the folder name
                arcname = os.path.relpath(file_path, start=os.path.dirname(addon_dir))
                zipf.write(file_path, arcname)
                
    print("Done!")

if __name__ == "__main__":
    create_addon_zip()
