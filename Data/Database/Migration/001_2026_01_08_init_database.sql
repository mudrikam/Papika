-- 001_2026_01_08_init_database.sql
-- Initial database schema (created 2026-01-08)

--------------- MIGRATIONS TABLE DEFINITION ----------------

CREATE TABLE migrations (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT NOT NULL UNIQUE,
    migration_applied_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

--------------- END OF MIGRATIONS TABLE DEFINITION ----------

--------------- IMAGES TABLE DEFINITION ----------------------

CREATE TABLE images (
    images_id INTEGER PRIMARY KEY AUTOINCREMENT,
    images_path TEXT NOT NULL UNIQUE,
    images_size INTEGER DEFAULT 0,
    images_extension TEXT,
    images_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    images_modified_at TEXT,
    images_accessed_at TEXT
);

--------------- END OF IMAGES TABLE DEFINITION --------------

--------------- EMBEDDINGS TABLE DEFINITION ------------------

CREATE TABLE embeddings (
    embeddings_id INTEGER PRIMARY KEY AUTOINCREMENT,
    embeddings_image_id INTEGER,
    embeddings_vector BLOB,
    embeddings_model TEXT,
    embeddings_dimension INTEGER,
    embeddings_device TEXT,
    embeddings_status TEXT DEFAULT 'pending',
    embeddings_processing_time REAL,
    embeddings_error TEXT,
    embeddings_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (embeddings_image_id) REFERENCES images(images_id) ON DELETE CASCADE
);

--------------- END OF EMBEDDINGS TABLE DEFINITION -----------

--------------- IMAGE_HASHES TABLE DEFINITION ----------------

CREATE TABLE image_hashes (
    image_hashes_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_hashes_image_id INTEGER,
    image_hashes_hash TEXT,
    image_hashes_algorithm TEXT,
    image_hashes_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (image_hashes_image_id) REFERENCES images(images_id) ON DELETE CASCADE
);

--------------- END OF IMAGE_HASHES TABLE DEFINITION ----------

--------------- IMAGE_GROUPS TABLE DEFINITION -----------------

CREATE TABLE image_groups (
    image_groups_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_groups_name TEXT NOT NULL UNIQUE,
    image_groups_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

--------------- END OF IMAGE_GROUPS TABLE DEFINITION ----------

--------------- IMAGE_GROUP_MEMBERS TABLE DEFINITION ----------

CREATE TABLE image_group_members (
    image_group_members_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_group_members_group_id INTEGER,
    image_group_members_image_id INTEGER,
    image_group_members_added_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (image_group_members_group_id) REFERENCES image_groups(image_groups_id) ON DELETE CASCADE,
    FOREIGN KEY (image_group_members_image_id) REFERENCES images(images_id) ON DELETE CASCADE
);

--------------- END OF IMAGE_GROUP_MEMBERS TABLE DEFINITION ---

--------------- CAPTIONS TABLE DEFINITION ----------------------

CREATE TABLE captions (
    captions_id INTEGER PRIMARY KEY AUTOINCREMENT,
    captions_image_id INTEGER,
    captions_caption TEXT,
    captions_model TEXT,
    captions_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (captions_image_id) REFERENCES images(images_id) ON DELETE CASCADE
);

--------------- END OF CAPTIONS TABLE DEFINITION --------------

--------------- IDENTIFIABLE_PERSONS TABLE DEFINITION --------

CREATE TABLE identifiable_persons (
    identifiable_persons_id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiable_persons_name TEXT,
    identifiable_persons_image_id INTEGER,
    identifiable_persons_confidence REAL,
    identifiable_persons_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (identifiable_persons_image_id) REFERENCES images(images_id) ON DELETE CASCADE
);

--------------- END OF IDENTIFIABLE_PERSONS TABLE DEFINITION -

--------------- IMAGE_CLUSTERS TABLE DEFINITION -------------

CREATE TABLE image_clusters (
    image_clusters_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_clusters_name TEXT NOT NULL UNIQUE,
    image_clusters_algorithm TEXT,
    image_clusters_parameters TEXT,
    image_clusters_created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

--------------- END OF IMAGE_CLUSTERS TABLE DEFINITION -------

--------------- IMAGE_CLUSTER_MEMBERS TABLE DEFINITION -------

CREATE TABLE image_cluster_members (
    image_cluster_members_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_cluster_members_cluster_id INTEGER,
    image_cluster_members_image_id INTEGER,
    image_cluster_members_added_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (image_cluster_members_cluster_id) REFERENCES image_clusters(image_clusters_id) ON DELETE CASCADE,
    FOREIGN KEY (image_cluster_members_image_id) REFERENCES images(images_id) ON DELETE CASCADE
);

--------------- END OF IMAGE_CLUSTER_MEMBERS TABLE DEFINITION -