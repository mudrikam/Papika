import sqlite3
from pathlib import Path


class DatabaseMigration:
    def __init__(self, db_path: Path, migration_dir: Path):
        self.db_path = db_path
        self.migration_dir = migration_dir
    
    def initialize_database(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()
    
    def run_migrations(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='migrations'
        """)
        
        if not cursor.fetchone():
            migration_files = sorted(self.migration_dir.glob("*.sql"))
            
            for migration_file in migration_files:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                cursor.executescript(sql_content)
                
                cursor.execute("""
                    INSERT INTO migrations (migration_name, migration_applied_at)
                    VALUES (?, datetime('now'))
                """, (migration_file.name,))
                
                conn.commit()
                print(f"Applied migration: {migration_file.name}")
        else:
            cursor.execute("SELECT migration_name FROM migrations")
            applied_migrations = {row[0] for row in cursor.fetchall()}
            
            migration_files = sorted(self.migration_dir.glob("*.sql"))
            
            for migration_file in migration_files:
                if migration_file.name not in applied_migrations:
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    cursor.executescript(sql_content)
                    
                    cursor.execute("""
                        INSERT INTO migrations (migration_name, migration_applied_at)
                        VALUES (?, datetime('now'))
                    """, (migration_file.name,))
                    
                    conn.commit()
                    print(f"Applied migration: {migration_file.name}")
        
        conn.close()
    
    def get_applied_migrations(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='migrations'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return []
        
        cursor.execute("""
            SELECT migration_name, migration_applied_at 
            FROM migrations 
            ORDER BY migration_applied_at
        """)
        
        migrations = cursor.fetchall()
        conn.close()
        
        return migrations
