import json
import hashlib
from pathlib import Path
from datetime import datetime
import platform
import subprocess
import ctypes
import os
from Configs.configs_file_manager import load_config
from Data.Database.Manager.database_migration import DatabaseMigration
from Data.Database.Manager.database_manager import DatabaseManager


def _make_hidden(path: Path):
    system = platform.system()
    try:
        if system == 'Windows':
            FILE_ATTRIBUTE_HIDDEN = 0x02
            rc = ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)
            if not rc:
                print(f"Failed to set hidden attribute on Windows for {path}")
        elif system == 'Darwin':
            subprocess.run(["chflags", "hidden", str(path)], check=True)
        else:
            if not path.name.startswith('.'):
                new_path = path.with_name('.' + path.name)
                try:
                    path.rename(new_path)
                    return new_path
                except Exception as e:
                    print(f"Failed to rename folder to hidden on Linux: {e}")
    except Exception as e:
        print(f"Failed to hide folder {path}: {e}")
    return path


def scan_directory(directory_path: Path, base_path: Path):
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Invalid directory: {directory_path}")
    
    configs = load_config(base_path)
    
    footprints_folder = directory_path / configs['database']['directory']
    footprints_folder.mkdir(parents=True, exist_ok=True)
    footprints_folder = _make_hidden(footprints_folder)
    
    db_path = footprints_folder / configs['database']['name']
    db_exists = db_path.exists()
    
    migration_dir = base_path / 'Data' / 'Database' / 'Migration'
    
    db_migration = DatabaseMigration(db_path, migration_dir)
    db_migration.initialize_database()
    db_migration.run_migrations()
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
    detected_images = []
    other_files = []
    
    for file_path in directory_path.rglob('*'):
        try:
            if file_path.is_file():
                if file_path.suffix.lower() in image_extensions:
                    detected_images.append(file_path)
                else:
                    other_files.append(file_path)
        except (PermissionError, OSError) as e:
            print(f"Permission denied accessing {file_path}: {e}")
            continue
    
    db_manager = DatabaseManager(db_path)
    db_manager.connect()
    
    current_image_paths = {str(img) for img in detected_images}
    db_images = db_manager.get_all_images()
    db_image_paths = {row['images_path']: row['images_id'] for row in db_images}
    
    inserted_count = 0
    updated_count = 0
    deleted_count = 0
    
    for db_path_str, db_image_id in list(db_image_paths.items()):
        if db_path_str not in current_image_paths:
            db_manager.delete_image(db_image_id)
            deleted_count += 1
            print(f"Deleted missing image from DB: {db_path_str}")
    
    for image_path in detected_images:
        try:
            stat = image_path.stat()
            size = stat.st_size
            extension = image_path.suffix.lower()
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            accessed_at = datetime.fromtimestamp(stat.st_atime).isoformat()
            
            image_path_str = str(image_path)
            existing = db_manager.get_image_by_path(image_path_str)
            
            if existing:
                if (existing['images_size'] != size or 
                    existing['images_modified_at'] != modified_at):
                    db_manager.update_image(existing['images_id'], size, modified_at, accessed_at)
                    updated_count += 1
            else:
                db_manager.insert_image(image_path_str, size, extension, modified_at, accessed_at)
                inserted_count += 1
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
    
    db_manager.disconnect()
    
    print(f"Database sync: {inserted_count} inserted, {updated_count} updated, {deleted_count} deleted")
    
    folder_hash = hashlib.sha256(str(directory_path).encode()).hexdigest()[:16]
    current_timestamp = datetime.now().isoformat()
    
    trails_data = {
        'path_folder': str(directory_path),
        'folder_session_hash': folder_hash,
        'files_count': len(detected_images) + len(other_files),
        'detected_image_files': len(detected_images),
        'other_files': len(other_files),
        'last_scan': current_timestamp,
        'last_access': current_timestamp
    }
    
    trails_json_path = footprints_folder / 'papika_trails.json'
    with open(trails_json_path, 'w', encoding='utf-8') as f:
        json.dump(trails_data, f, indent=2)
    
    if db_exists:
        print(f"Database updated at: {db_path}")
        print(f"Trails JSON updated at: {trails_json_path}")
    else:
        print(f"Database created at: {db_path}")
        print(f"Trails JSON created at: {trails_json_path}")
    
    print(f"Found {len(detected_images)} images and {len(other_files)} other files")
    
    return trails_data
