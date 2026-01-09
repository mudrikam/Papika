import shutil
from pathlib import Path
from Configs.configs_file_manager import load_config


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
