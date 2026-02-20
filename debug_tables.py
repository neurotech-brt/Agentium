import sqlalchemy
from sqlalchemy import inspect

engine = sqlalchemy.create_engine("postgresql://agentium:agentium@localhost:5432/agentium")
inspector = inspect(engine)

print("Tables in 'agentium' database:")
for table_name in inspector.get_table_names():
    print(f" - {table_name}")
