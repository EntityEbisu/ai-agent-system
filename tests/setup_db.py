#!/usr/bin/env python
"""
Database initialization script for Level 300 persistence.

Run this once to set up SQLite database with all tables.
Usage:
    python scripts/setup_db.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.models import init_db, Base


def main():
    """Initialize database."""
    db_path = project_root / "data" / "sqlite"
    db_path.mkdir(parents=True, exist_ok=True)
    
    database_url = f"sqlite:///{db_path}/conversations.db"
    print(f"Initializing database at: {database_url}")
    
    Session, engine = init_db(database_url)
    print("✅ Database initialized successfully!")
    
    # Print schema info
    print("\nCreated tables:")
    for table in Base.metadata.tables:
        print(f"  - {table}")
    
    print("\nTo use the database in your code:")
    print(f'  from app.data.models import init_db')
    print(f'  Session, engine = init_db("{database_url}")')
    print(f'  session = Session()')


if __name__ == "__main__":
    main()
