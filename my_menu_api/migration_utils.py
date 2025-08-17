"""
Migration utilities for database operations.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from .database import DATABASE_URL, engine
from .logging_config import structured_logger


class MigrationManager:
    """Utility class for managing database migrations."""
    
    def __init__(self, alembic_cfg_path: Optional[str] = None):
        """Initialize migration manager."""
        if alembic_cfg_path is None:
            # Look for alembic.ini in project root
            project_root = Path(__file__).parent.parent
            alembic_cfg_path = project_root / "alembic.ini"
        
        self.alembic_cfg_path = Path(alembic_cfg_path)
        self.config = Config(str(self.alembic_cfg_path))
        
        # Set the database URL from environment or config
        database_url = os.getenv("DATABASE_URL", DATABASE_URL)
        self.config.set_main_option("sqlalchemy.url", database_url)
    
    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration."""
        try:
            structured_logger.info(
                "Creating new migration",
                message=message,
                autogenerate=autogenerate
            )
            
            # Create the migration
            revision = command.revision(
                self.config,
                message=message,
                autogenerate=autogenerate
            )
            
            structured_logger.info(
                "Migration created successfully",
                revision=revision.revision,
                message=message
            )
            
            return revision.revision
            
        except Exception as e:
            structured_logger.error(
                "Failed to create migration",
                error=str(e),
                message=message
            )
            raise
    
    def upgrade_database(self, revision: str = "head") -> None:
        """Upgrade database to specified revision."""
        try:
            structured_logger.info(
                "Starting database upgrade",
                target_revision=revision
            )
            
            command.upgrade(self.config, revision)
            
            structured_logger.info(
                "Database upgrade completed",
                target_revision=revision
            )
            
        except Exception as e:
            structured_logger.error(
                "Database upgrade failed",
                error=str(e),
                target_revision=revision
            )
            raise
    
    def downgrade_database(self, revision: str) -> None:
        """Downgrade database to specified revision."""
        try:
            structured_logger.info(
                "Starting database downgrade",
                target_revision=revision
            )
            
            command.downgrade(self.config, revision)
            
            structured_logger.info(
                "Database downgrade completed",
                target_revision=revision
            )
            
        except Exception as e:
            structured_logger.error(
                "Database downgrade failed",
                error=str(e),
                target_revision=revision
            )
            raise
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                row = result.fetchone()
                return row[0] if row else None
                
        except OperationalError:
            # Alembic version table doesn't exist yet
            return None
        except Exception as e:
            structured_logger.error(
                "Failed to get current revision",
                error=str(e)
            )
            return None
    
    def get_migration_history(self) -> List[dict]:
        """Get migration history."""
        try:
            script_dir = ScriptDirectory.from_config(self.config)
            revisions = []
            
            for revision in script_dir.walk_revisions():
                revisions.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": revision.branch_labels,
                    "message": revision.doc,
                    "path": revision.path
                })
            
            return revisions
            
        except Exception as e:
            structured_logger.error(
                "Failed to get migration history",
                error=str(e)
            )
            return []
    
    def validate_migrations(self) -> bool:
        """Validate that migrations are in sync with models."""
        try:
            # Check if there are pending migrations
            script_dir = ScriptDirectory.from_config(self.config)
            current_rev = self.get_current_revision()
            head_rev = script_dir.get_current_head()
            
            if current_rev != head_rev:
                structured_logger.warning(
                    "Database is not up to date",
                    current_revision=current_rev,
                    head_revision=head_rev
                )
                return False
            
            # TODO: Add model vs database schema comparison
            structured_logger.info("Migration validation passed")
            return True
            
        except Exception as e:
            structured_logger.error(
                "Migration validation failed",
                error=str(e)
            )
            return False
    
    def reset_database(self) -> None:
        """Reset database by dropping all tables and rerunning migrations."""
        try:
            structured_logger.warning("Resetting database - all data will be lost")
            
            # Drop all tables
            from .models import Base
            Base.metadata.drop_all(bind=engine)
            
            # Run migrations from scratch
            self.upgrade_database("head")
            
            structured_logger.info("Database reset completed")
            
        except Exception as e:
            structured_logger.error(
                "Database reset failed",
                error=str(e)
            )
            raise
    
    def check_migration_environment(self) -> dict:
        """Check migration environment setup."""
        checks = {
            "alembic_ini_exists": self.alembic_cfg_path.exists(),
            "versions_directory_exists": False,
            "env_py_exists": False,
            "database_connectable": False,
            "alembic_version_table_exists": False
        }
        
        try:
            # Check versions directory
            versions_dir = self.alembic_cfg_path.parent / "alembic" / "versions"
            checks["versions_directory_exists"] = versions_dir.exists()
            
            # Check env.py
            env_py = self.alembic_cfg_path.parent / "alembic" / "env.py"
            checks["env_py_exists"] = env_py.exists()
            
            # Check database connectivity
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                checks["database_connectable"] = True
                
                # Check if alembic_version table exists
                try:
                    connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                    checks["alembic_version_table_exists"] = True
                except OperationalError:
                    pass
            
        except Exception as e:
            structured_logger.error(
                "Migration environment check failed",
                error=str(e)
            )
        
        return checks


# Global migration manager instance
migration_manager = MigrationManager()


def init_alembic():
    """Initialize Alembic for the project."""
    try:
        # Check if already initialized
        checks = migration_manager.check_migration_environment()
        
        if not checks["alembic_ini_exists"]:
            structured_logger.error("alembic.ini not found")
            return False
        
        if not checks["database_connectable"]:
            structured_logger.error("Cannot connect to database")
            return False
        
        # Create initial migration if alembic_version table doesn't exist
        if not checks["alembic_version_table_exists"]:
            structured_logger.info("Initializing Alembic version control")
            command.stamp(migration_manager.config, "head")
        
        structured_logger.info("Alembic initialization completed")
        return True
        
    except Exception as e:
        structured_logger.error(
            "Alembic initialization failed",
            error=str(e)
        )
        return False


def run_migrations():
    """Run pending migrations."""
    try:
        if not init_alembic():
            return False
        
        migration_manager.upgrade_database("head")
        return True
        
    except Exception as e:
        structured_logger.error(
            "Migration execution failed",
            error=str(e)
        )
        return False


if __name__ == "__main__":
    """CLI interface for migration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument("command", choices=[
        "init", "migrate", "upgrade", "downgrade", 
        "current", "history", "validate", "reset"
    ])
    parser.add_argument("--message", "-m", help="Migration message")
    parser.add_argument("--revision", "-r", help="Target revision")
    
    args = parser.parse_args()
    
    if args.command == "init":
        success = init_alembic()
        sys.exit(0 if success else 1)
    
    elif args.command == "migrate":
        if not args.message:
            print("Migration message is required")
            sys.exit(1)
        
        try:
            revision = migration_manager.create_migration(args.message)
            print(f"Created migration: {revision}")
        except Exception as e:
            print(f"Failed to create migration: {e}")
            sys.exit(1)
    
    elif args.command == "upgrade":
        try:
            revision = args.revision or "head"
            migration_manager.upgrade_database(revision)
            print(f"Upgraded to: {revision}")
        except Exception as e:
            print(f"Failed to upgrade: {e}")
            sys.exit(1)
    
    elif args.command == "downgrade":
        if not args.revision:
            print("Target revision is required for downgrade")
            sys.exit(1)
        
        try:
            migration_manager.downgrade_database(args.revision)
            print(f"Downgraded to: {args.revision}")
        except Exception as e:
            print(f"Failed to downgrade: {e}")
            sys.exit(1)
    
    elif args.command == "current":
        current = migration_manager.get_current_revision()
        print(f"Current revision: {current or 'None'}")
    
    elif args.command == "history":
        history = migration_manager.get_migration_history()
        for migration in history:
            print(f"{migration['revision']}: {migration['message']}")
    
    elif args.command == "validate":
        is_valid = migration_manager.validate_migrations()
        print(f"Migrations valid: {is_valid}")
        sys.exit(0 if is_valid else 1)
    
    elif args.command == "reset":
        confirm = input("This will delete all data. Type 'yes' to continue: ")
        if confirm.lower() == "yes":
            migration_manager.reset_database()
            print("Database reset completed")
        else:
            print("Reset cancelled")
