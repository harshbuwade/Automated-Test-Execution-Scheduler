#!/usr/bin/env python
"""Development-safe database initialization script.

Creates database tables from SQLAlchemy metadata when explicitly invoked.
"""
import os
import sys

# Ensure backend folder is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import init_db, engine


def main():
    print(f"Initializing database using engine: {engine.url}")
    init_db()
    print("Database tables created successfully!")


if __name__ == "__main__":
    main()
