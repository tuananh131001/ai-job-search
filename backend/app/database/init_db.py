"""
Database initialization script
Creates all tables and initial data
"""
from app.database.session import Base, engine
from app.models import Company, Job  # Import models to register them


def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_all_tables():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped!")


if __name__ == "__main__":
    init_db()