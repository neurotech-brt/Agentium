import sys
from sqlalchemy import MetaData, Table, create_engine
from backend.core.config import settings

def check():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    metadata = MetaData()
    audit_logs = Table('audit_logs', metadata, autoload_with=engine)
    print("Columns for audit_logs:")
    for col in audit_logs.columns:
        print("- ", col.name, type(col.type))

if __name__ == "__main__":
    check()
