"""
Database Manager for @donhustle_bot
Handles SQLite database connections, initialization, and migrations
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import Optional, Any, Dict, List
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages SQLite database connections and operations for the bot.
    Handles initialization, migrations, and provides connection management.
    """
    
    def __init__(self, db_path: str = "bot_database.db"):
        """
        Initialize the DatabaseManager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[sqlite3.Connection] = None
        
        # Ensure database directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database on first run
        self.initialize_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with proper configuration.
        
        Returns:
            SQLite connection object
        """
        if self._connection is None or self._connection.execute("PRAGMA quick_check").fetchone() is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable foreign key constraints
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Set row factory for dict-like access
            self._connection.row_factory = sqlite3.Row
            
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database operations with automatic commit/rollback.
        
        Yields:
            SQLite cursor object
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()
    
    def initialize_database(self) -> None:
        """
        Initialize the database with the schema if it doesn't exist.
        """
        try:
            schema_path = Path(__file__).parent / "schema.sql"
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            with self.get_cursor() as cursor:
                # Execute schema creation
                cursor.executescript(schema_sql)
                
                # Set initial database version
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Check if version already exists
                cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                current_version = cursor.fetchone()
                
                if current_version is None:
                    cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
                    self.logger.info("Database initialized with schema version 1")
                else:
                    self.logger.info(f"Database already initialized with version {current_version[0]}")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_schema_version(self) -> int:
        """
        Get the current schema version.
        
        Returns:
            Current schema version number
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.OperationalError:
            # Table doesn't exist, assume version 0
            return 0
    
    def apply_migration(self, version: int, migration_sql: str) -> bool:
        """
        Apply a database migration.
        
        Args:
            version: Migration version number
            migration_sql: SQL statements to execute
            
        Returns:
            True if migration was applied successfully
        """
        current_version = self.get_schema_version()
        
        if version <= current_version:
            self.logger.info(f"Migration {version} already applied (current: {current_version})")
            return True
        
        try:
            with self.get_cursor() as cursor:
                # Execute migration
                cursor.executescript(migration_sql)
                
                # Update version
                cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
                
                self.logger.info(f"Successfully applied migration {version}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to apply migration {version}: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT query and return the last row ID.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            ID of the inserted row
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self._connection:
            self._connection.close()
            self._connection = None
            self.logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(db_path: str = "bot_database.db") -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    
    return _db_manager


def close_database():
    """
    Close the global database connection.
    """
    global _db_manager
    
    if _db_manager:
        _db_manager.close()
        _db_manager = None