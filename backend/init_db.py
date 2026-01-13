import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self, db_path='recommendation.db', schema_path='db_schema.sql'):
        self.db_path = db_path
        self.schema_path = schema_path

    def initialize_database(self):
        """Reads db_schema.sql and creates all tables if they don't exist."""
        if not os.path.exists(self.schema_path):
            logger.error(f"Schema file not found at {self.schema_path}")
            return False

        try:
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()

            conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully.")
            return self.verify_schema()
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            return False

    def verify_schema(self):
        """Verifies that all required tables exist in the database."""
        required_tables = ['user_mood_profile', 'mood_history', 'watch_sessions', 'addiction_metrics']
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                logger.info("Schema verification passed.")
                return True
            else:
                logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error verifying schema: {e}")
            return False

    def reset_database(self):
        """Drops all tables and re-initializes for testing."""
        logger.info("Resetting database...")
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            return self.initialize_database()
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            return False

if __name__ == "__main__":
    db_init = DatabaseInitializer()
    db_init.initialize_database()
