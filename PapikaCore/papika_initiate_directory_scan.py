import json
import hashlib
from pathlib import Path
from datetime import datetime
import platform
import subprocess
import ctypes
import os
from PySide6.QtCore import QThread, Signal, QCoreApplication, Qt
from Configs.configs_file_manager import load_config
from Data.Database.Manager.database_migration import DatabaseMigration
from Data.Database.Manager.database_manager import DatabaseManager
from UI.Dialogs.global_progress_dialog import GlobalProgressDialog


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


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}


class DirectoryScanThread(QThread):
    progress_updated = Signal(int, int, str, str)
    scan_completed = Signal(dict)
    scan_error = Signal(str)
    
    def __init__(self, directory_path: Path, base_path: Path, existing_images=None, parent=None):
        super().__init__(parent)
        self.directory_path = directory_path
        self.base_path = base_path
        self.existing_images = existing_images
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
    
    def run(self):
        try:
            trails_data = self._execute_scan()
            if not self._is_cancelled and trails_data:
                self.scan_completed.emit(trails_data)
        except Exception as e:
            print(f"Error during directory scan: {e}")
            self.scan_error.emit(str(e))
    
    def _execute_scan(self):
        configs = load_config(self.base_path)
        footprints_folder_name = configs['database']['directory']
        
        footprints_folder = self.directory_path / footprints_folder_name
        footprints_folder.mkdir(parents=True, exist_ok=True)
        footprints_folder = _make_hidden(footprints_folder)
        
        db_path = footprints_folder / configs['database']['name']
        
        migration_dir = self.base_path / 'Data' / 'Database' / 'Migration'
        db_migration = DatabaseMigration(db_path, migration_dir)
        db_migration.initialize_database()
        db_migration.run_migrations()
        
        if self.existing_images is not None:
            image_files = [Path(img) if isinstance(img, str) else img for img in self.existing_images]
            total_images = len(image_files)
            other_count = 0
        else:
            image_files = []
            other_count = 0
            
            for f in self.directory_path.rglob('*'):
                if self._is_cancelled:
                    return {}
                
                if f.is_file() and footprints_folder_name not in f.parts:
                    if f.suffix.lower() in IMAGE_EXTENSIONS:
                        image_files.append(f)
                    else:
                        other_count += 1
            
            total_images = len(image_files)
        
        if total_images == 0:
            self.progress_updated.emit(1, 1, "No images found", "")
            return self._create_trails_data(0, other_count, footprints_folder)
        
        db_manager = DatabaseManager(db_path)
        db_manager.connect()
        
        current_image_paths = {str(img) for img in image_files}
        db_images = db_manager.get_all_images()
        db_image_paths = {row['images_path']: row['images_id'] for row in db_images}
        
        inserted_count = 0
        updated_count = 0
        deleted_count = 0
        
        images_to_delete = [(db_path_str, db_image_id) for db_path_str, db_image_id in db_image_paths.items() 
                           if db_path_str not in current_image_paths]
        
        total_delete = len(images_to_delete)
        if total_delete > 0:
            for idx, (db_path_str, db_image_id) in enumerate(images_to_delete):
                if self._is_cancelled:
                    db_manager.disconnect()
                    return {}
                
                db_manager.delete_image(db_image_id)
                deleted_count += 1
                
                if (idx + 1) % 20 == 0 or idx == total_delete - 1:
                    self.progress_updated.emit(
                        idx + 1,
                        total_delete,
                        f"Removing: {idx + 1} of {total_delete}",
                        f"{deleted_count} deleted"
                    )
        
        batch_inserts = []
        batch_updates = []
        processed = 0
        
        for image_path in image_files:
            if self._is_cancelled:
                db_manager.disconnect()
                return {}
            
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
                        batch_updates.append((existing['images_id'], size, modified_at, accessed_at))
                else:
                    batch_inserts.append((image_path_str, size, extension, modified_at, accessed_at))
            except Exception as e:
                print(f"Error processing image {image_path}: {e}")
            
            processed += 1
            
            if len(batch_inserts) >= 100:
                db_manager.batch_insert_images(batch_inserts)
                inserted_count += len(batch_inserts)
                batch_inserts = []
            
            if len(batch_updates) >= 100:
                db_manager.batch_update_images(batch_updates)
                updated_count += len(batch_updates)
                batch_updates = []
            
            if processed % 100 == 0 or processed == total_images:
                if batch_inserts:
                    db_manager.batch_insert_images(batch_inserts)
                    inserted_count += len(batch_inserts)
                    batch_inserts = []
                
                if batch_updates:
                    db_manager.batch_update_images(batch_updates)
                    updated_count += len(batch_updates)
                    batch_updates = []
                
                self.progress_updated.emit(
                    processed,
                    total_images,
                    f"Processing: {processed} of {total_images}",
                    f"{inserted_count} inserted, {updated_count} updated, {deleted_count} deleted"
                )
        
        if batch_inserts:
            db_manager.batch_insert_images(batch_inserts)
            inserted_count += len(batch_inserts)
        
        if batch_updates:
            db_manager.batch_update_images(batch_updates)
            updated_count += len(batch_updates)
        
        db_manager.disconnect()
        
        print(f"Scan complete: {inserted_count} inserted, {updated_count} updated, {deleted_count} deleted")
        
        return self._create_trails_data(total_images, other_count, footprints_folder)
    
    def _create_trails_data(self, image_count, other_count, footprints_folder):
        folder_hash = hashlib.sha256(str(self.directory_path).encode()).hexdigest()[:16]
        current_timestamp = datetime.now().isoformat()
        
        trails_data = {
            'path_folder': str(self.directory_path),
            'folder_session_hash': folder_hash,
            'files_count': image_count + other_count,
            'detected_image_files': image_count,
            'other_files': other_count,
            'last_scan': current_timestamp,
            'last_access': current_timestamp
        }
        
        trails_json_path = footprints_folder / 'papika_trails.json'
        with open(trails_json_path, 'w', encoding='utf-8') as f:
            json.dump(trails_data, f, indent=2)
        
        return trails_data


def scan_directory(directory_path: Path, base_path: Path, parent_widget=None, existing_images=None):
    if not directory_path.exists() or not directory_path.is_dir():
        raise ValueError(f"Invalid directory: {directory_path}")
    
    progress_dialog = GlobalProgressDialog(
        parent=parent_widget,
        title="Directory Scan",
        initial_message="Inserting to database..."
    )
    
    scan_thread = DirectoryScanThread(directory_path, base_path, existing_images)
    scan_result = {}
    
    def on_progress_updated(value, maximum, message, detail):
        progress_dialog.update_progress(value, maximum)
        progress_dialog.set_message(message)
        progress_dialog.set_detail(detail)
    
    def on_scan_completed(trails_data):
        nonlocal scan_result
        scan_result = trails_data
        progress_dialog.close()
    
    def on_scan_error(error_message):
        print(f"Scan error: {error_message}")
        progress_dialog.close()
    
    def on_cancel_requested():
        scan_thread.cancel()
        progress_dialog.close()
    
    scan_thread.progress_updated.connect(on_progress_updated, Qt.QueuedConnection)
    scan_thread.scan_completed.connect(on_scan_completed, Qt.QueuedConnection)
    scan_thread.scan_error.connect(on_scan_error, Qt.QueuedConnection)
    progress_dialog.cancel_requested.connect(on_cancel_requested, Qt.DirectConnection)
    
    scan_thread.start()
    progress_dialog.exec()
    
    return scan_result
