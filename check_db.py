import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
print("DATABASE_URL:", url)
if not url:
    print("ERROR: DATABASE_URL not set")
    raise SystemExit(1)

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("DB OK, SELECT 1 =>", list(result))
except Exception as e:
    print("DB ERROR:", repr(e))
    raise
