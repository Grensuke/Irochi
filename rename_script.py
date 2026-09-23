import os
import re

ROOT_DIR = r"c:\Users\STARK\Documents\Vibhinetra"

EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.pytest_cache'}
EXCLUDE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.pdf', '.joblib', '.pyc'}

REPLACEMENTS = [
    ("Vibhinetra", "Vibhinetra"),
    ("vibhinetra", "vibhinetra"),
    ("VIBHINETRA", "VIBHINETRA")
]

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        # Might be binary or encoding issue, skip
        return False

    new_content = content
    for old_str, new_str in REPLACEMENTS:
        new_content = new_content.replace(old_str, new_str)
        
    if new_content != content:
        # Preserve original line endings by re-reading with newline=''
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            orig_content = f.read()
            
        new_content = orig_content
        for old_str, new_str in REPLACEMENTS:
            new_content = new_content.replace(old_str, new_str)
            
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(new_content)
        return True
    return False

def main():
    modified_files = []
    for root, dirs, files in os.walk(ROOT_DIR):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTS:
                continue
                
            filepath = os.path.join(root, file)
            if replace_in_file(filepath):
                modified_files.append(filepath)
                
    print(f"Modified {len(modified_files)} files:")
    for f in modified_files:
        print(f" - {f.replace(ROOT_DIR, '')}")

if __name__ == "__main__":
    main()
