import sqlalchemy
from sqlalchemy import inspect

engine = sqlalchemy.create_engine("postgresql://agentium:agentium@localhost:5432/agentium")
inspector = inspect(engine)

tables_to_check = ['agents', 'users', 'tasks', 'task_audit_logs']

print("Verifying 'deleted_at' column in tables:")
for table_name in tables_to_check:
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    if 'deleted_at' in columns:
        print(f" [OK] {table_name}: 'deleted_at' exists")
    else:
        print(f" [FAIL] {table_name}: 'deleted_at' MISSING")

print("\nVerifying 'is_active' type in 'agents':")
columns = inspector.get_columns('agents')
for c in columns:
    if c['name'] == 'is_active':
        print(f" agents.is_active type: {c['type']}")
