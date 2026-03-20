import os
from fastapi import FastAPI, Response, status
from sqlalchemy import create_engine, text
from minio import Minio
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/ocrdb")
MINIO_URL = os.getenv("MINIO_URL", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def read_health():
    return "OK"

@app.get("/status")
def get_status(response: Response):
    health_report = {
        "status": "OK",
        "database": "Unknown",
        "minio": "Unknown",
    }

    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_report["database"] = "Connected"
    except Exception as e:
        health_report["database"] = f"Error: {str(e)}"
        health_report["status"] = "Error"

    try:
        client = Minio(
            MINIO_URL.replace("http://", ""),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        client.list_buckets()
        health_report["minio"] = "Connected"
    except Exception as e:
        health_report["minio"] = f"Error: {str(e)}"
        health_report["status"] = "Error"

    if health_report["status"] == "Error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_report

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}