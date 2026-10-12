
from sqlalchemy import create_engine,  URL
import os
from sqlalchemy.orm import sessionmaker

DB_PASSWORD = os.getenv("MYSQL_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError("MYSQL_PASSWORD is not set")

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password=DB_PASSWORD,
    host="localhost",
    port=3306,
    database="api_gateway_db"
)

engine = create_engine(DATABASE_URL)

SessionLocal=sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

   