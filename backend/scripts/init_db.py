#!/usr/bin/env python3
"""
Database initialization script for Docker.
Waits for PostgreSQL, runs Alembic migrations.
"""

import os
import sys
import time
import socket
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def wait_for_postgres(host: str = "postgres", port: int = 5432, timeout: int = 60):
    """Wait for PostgreSQL to be ready."""
    logger.info(f"⏳ Waiting for PostgreSQL at {host}:{port}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((host, port))
            sock.close()
            logger.info("✅ PostgreSQL is ready!")
            return True
        except (socket.error, socket.timeout):
            time.sleep(1)
    
    logger.error(f"❌ PostgreSQL not ready after {timeout}s")
    return False


def run_migrations():
    """Run Alembic migrations."""
    logger.info("🔄 Running Alembic migrations...")
    
    # Get alembic.ini path (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    alembic_ini = os.path.join(backend_dir, "alembic", "alembic.ini")
    
    # Or use environment variable
    if not os.path.exists(alembic_ini):
        alembic_ini = os.path.join(backend_dir, "alembic.ini")
    
    result = subprocess.run(
        ["alembic", "-c", alembic_ini, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"❌ Migration failed:\n{result.stderr}")
        sys.exit(1)
    
    logger.info("✅ Migrations completed!")
    if result.stdout:
        logger.info(result.stdout)


def stamp_if_fresh():
    """Stamp database as current if it has tables but no alembic version."""
    # Check if alembic_version table exists
    result = subprocess.run(
        ["alembic", "-c", "alembic.ini", "current"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True,
        text=True
    )
    
    if "None" in result.stdout or result.returncode != 0:
        logger.info("📌 Stamping fresh database...")
        subprocess.run(
            ["alembic", "-c", "alembic.ini", "stamp", "head"],
            check=True
        )


def main():
    """Main entry point."""
    # Get config from environment
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    
    # Wait for database
    if not wait_for_postgres(pg_host, pg_port):
        sys.exit(1)
    
    # Run migrations
    run_migrations()
    
    logger.info("🎉 Database initialization complete!")


if __name__ == "__main__":
    main()