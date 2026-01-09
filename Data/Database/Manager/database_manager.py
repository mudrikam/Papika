import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute_query(self, query, params=None):
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query, params=None):
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def insert_image(self, image_path, size, extension, modified_at=None, accessed_at=None):
        query = """
            INSERT INTO images (images_path, images_size, images_extension, images_modified_at, images_accessed_at)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.execute_query(query, (image_path, size, extension, modified_at, accessed_at))
        return cursor.lastrowid
    
    def batch_insert_images(self, images_data):
        if not images_data:
            return 0
        
        query = """
            INSERT INTO images (images_path, images_size, images_extension, images_modified_at, images_accessed_at)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.conn.cursor()
        cursor.executemany(query, images_data)
        self.conn.commit()
        return len(images_data)
    
    def get_image_by_path(self, image_path):
        query = "SELECT * FROM images WHERE images_path = ?"
        return self.fetch_one(query, (image_path,))
    
    def get_all_images(self):
        query = "SELECT * FROM images"
        return self.fetch_all(query)
    
    def delete_image(self, image_id):
        query = "DELETE FROM images WHERE images_id = ?"
        self.execute_query(query, (image_id,))
    
    def update_image(self, image_id, size=None, modified_at=None, accessed_at=None):
        updates = []
        params = []
        
        if size is not None:
            updates.append("images_size = ?")
            params.append(size)
        
        if modified_at is not None:
            updates.append("images_modified_at = ?")
            params.append(modified_at)
        
        if accessed_at is not None:
            updates.append("images_accessed_at = ?")
            params.append(accessed_at)
        
        if not updates:
            return
        
        params.append(image_id)
        query = f"UPDATE images SET {', '.join(updates)} WHERE images_id = ?"
        self.execute_query(query, params)
    
    def batch_update_images(self, updates_data):
        if not updates_data:
            return 0
        
        query = "UPDATE images SET images_size = ?, images_modified_at = ?, images_accessed_at = ? WHERE images_id = ?"
        batch_params = [(size, modified_at, accessed_at, image_id) for image_id, size, modified_at, accessed_at in updates_data]
        
        cursor = self.conn.cursor()
        cursor.executemany(query, batch_params)
        self.conn.commit()
        
        return len(updates_data)
    
    def clear_all_images(self):
        query = "DELETE FROM images"
        self.execute_query(query)
    
    def insert_embedding(self, image_id, vector, model, dimension, device, status='pending', processing_time=None, error=None):
        query = """
            INSERT INTO image_embeddings (image_embeddings_image_id, image_embeddings_vector, image_embeddings_model, 
                                   image_embeddings_dimension, image_embeddings_device, image_embeddings_status,
                                   image_embeddings_processing_time, image_embeddings_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.execute_query(query, (image_id, vector, model, dimension, device, status, processing_time, error))
        return cursor.lastrowid
    
    def get_embeddings_by_image_id(self, image_id):
        query = "SELECT * FROM image_embeddings WHERE image_embeddings_image_id = ?"
        return self.fetch_all(query, (image_id,))
    
    def insert_image_hash(self, image_id, hash_value, algorithm):
        query = """
            INSERT INTO image_hashes (image_hashes_image_id, image_hashes_hash, image_hashes_algorithm)
            VALUES (?, ?, ?)
        """
        cursor = self.execute_query(query, (image_id, hash_value, algorithm))
        return cursor.lastrowid
    
    def get_image_hash_by_image_id(self, image_id, algorithm=None):
        if algorithm:
            query = "SELECT * FROM image_hashes WHERE image_hashes_image_id = ? AND image_hashes_algorithm = ?"
            return self.fetch_one(query, (image_id, algorithm))
        else:
            query = "SELECT * FROM image_hashes WHERE image_hashes_image_id = ?"
            return self.fetch_all(query, (image_id,))
    
    def insert_caption(self, image_id, caption, model):
        query = """
            INSERT INTO image_captions (image_captions_image_id, image_captions_caption, image_captions_model)
            VALUES (?, ?, ?)
        """
        cursor = self.execute_query(query, (image_id, caption, model))
        return cursor.lastrowid
    
    def get_captions_by_image_id(self, image_id):
        query = "SELECT * FROM image_captions WHERE image_captions_image_id = ?"
        return self.fetch_all(query, (image_id,))
    
    def create_image_group(self, group_name):
        query = "INSERT INTO image_groups (image_groups_name) VALUES (?)"
        cursor = self.execute_query(query, (group_name,))
        return cursor.lastrowid
    
    def add_image_to_group(self, group_id, image_id):
        query = """
            INSERT INTO image_group_members (image_group_members_group_id, image_group_members_image_id)
            VALUES (?, ?)
        """
        cursor = self.execute_query(query, (group_id, image_id))
        return cursor.lastrowid
    
    def get_images_in_group(self, group_id):
        query = """
            SELECT i.* FROM images i
            JOIN image_group_members igm ON i.images_id = igm.image_group_members_image_id
            WHERE igm.image_group_members_group_id = ?
        """
        return self.fetch_all(query, (group_id,))
    
    def insert_identifiable_person(self, name, image_id, confidence):
        query = """
            INSERT INTO identifiable_persons (identifiable_persons_name, identifiable_persons_image_id, 
                                            identifiable_persons_confidence)
            VALUES (?, ?, ?)
        """
        cursor = self.execute_query(query, (name, image_id, confidence))
        return cursor.lastrowid
    
    def get_persons_by_image_id(self, image_id):
        query = "SELECT * FROM identifiable_persons WHERE identifiable_persons_image_id = ?"
        return self.fetch_all(query, (image_id,))
    
    def create_image_cluster(self, cluster_name, algorithm, parameters):
        query = """
            INSERT INTO image_clusters (image_clusters_name, image_clusters_algorithm, image_clusters_parameters)
            VALUES (?, ?, ?)
        """
        cursor = self.execute_query(query, (cluster_name, algorithm, parameters))
        return cursor.lastrowid
    
    def add_image_to_cluster(self, cluster_id, image_id):
        query = """
            INSERT INTO image_cluster_members (image_cluster_members_cluster_id, image_cluster_members_image_id)
            VALUES (?, ?)
        """
        cursor = self.execute_query(query, (cluster_id, image_id))
        return cursor.lastrowid
    
    def get_images_in_cluster(self, cluster_id):
        query = """
            SELECT i.* FROM images i
            JOIN image_cluster_members icm ON i.images_id = icm.image_cluster_members_image_id
            WHERE icm.image_cluster_members_cluster_id = ?
        """
        return self.fetch_all(query, (cluster_id,))
