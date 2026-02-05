import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tasks.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'stress_level' not in columns:
        print("Adding stress_level column...")
        cursor.execute("ALTER TABLE tasks ADD COLUMN stress_level INTEGER NOT NULL DEFAULT 5")
    
    if 'depends_on_id' not in columns:
        print("Adding depends_on_id column...")
        cursor.execute("ALTER TABLE tasks ADD COLUMN depends_on_id INTEGER NOT NULL DEFAULT 0")
    
    conn.commit()
    conn.close()
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()