import json
import shutil
from pathlib import Path

from Configs.configs_file_manager import load_config


def is_scan_required(directory_path: Path, base_path: Path) -> bool:
    if not directory_path.exists() or not directory_path.is_dir():
        return False
    
    try:
        configs = load_config(base_path)
        footprints_folder = directory_path / configs['database']['directory']
        trails_json_path = footprints_folder / 'papika_trails.json'
        
        if not trails_json_path.exists():
            return True
        
        with open(trails_json_path, 'r', encoding='utf-8') as f:
            trails_data = json.load(f)
        
        stored_files_count = trails_data.get('files_count', 0)
        stored_images_count = trails_data.get('detected_image_files', 0)
        stored_other_count = trails_data.get('other_files', 0)
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
        actual_images = 0
        actual_other = 0
        
        for file_path in directory_path.rglob('*'):
            try:
                if file_path.is_file():
                    if file_path.suffix.lower() in image_extensions:
                        actual_images += 1
                    else:
                        actual_other += 1
            except (PermissionError, OSError):
                continue
        
        actual_total = actual_images + actual_other
        
        return (actual_total != stored_files_count or 
                actual_images != stored_images_count or 
                actual_other != stored_other_count)
    except Exception as e:
        print(f"Error checking if scan required: {e}")
        return False


def remove_footprints(directory_path: Path, base_path: Path):
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Invalid directory: {directory_path}")
    
    configs = load_config(base_path)
    footprints_folder = directory_path / configs['database']['directory']
    
    if not footprints_folder.exists():
        folder_name = directory_path.name if directory_path.name else str(directory_path)
        raise FileNotFoundError(f"Papika has not scanned folder '{folder_name}' yet")
    
    try:
        shutil.rmtree(footprints_folder)
        print(f"Successfully removed Papika's footprints from: {directory_path}")
        return True
    except Exception as e:
        print(f"Error removing footprints: {e}")
        raise
