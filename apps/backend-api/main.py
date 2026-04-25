import logging
import os
from typing import Generator
from uuid import uuid4
from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from minio import Minio
from dotenv import load_dotenv
from models import Base, Image
import ocr

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/ocrdb")
MINIO_URL = os.getenv("MINIO_URL", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")

logger.info(f"Database URL: {DB_URL}")
logger.info(f"MinIO URL: {MINIO_URL}")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

minio_client = Minio(
    MINIO_URL.replace("http://", ""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_minio() -> Minio:
    return minio_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def read_health():
    return "OK"

@app.get("/status")
def get_status(
    response: Response,
    db: Session = Depends(get_db),
    minio: Minio = Depends(get_minio),
):
    health_report = {
        "status": "OK",
        "database": "Unknown",
        "minio": "Unknown",
    }

    try:
        db.execute(text("SELECT 1"))
        health_report["database"] = "Connected"
    except Exception as e:
        health_report["database"] = f"Error: {str(e)}"
        health_report["status"] = "Error"
    try:
        minio.list_buckets()
        health_report["minio"] = "Connected"
    except Exception as e:
        health_report["minio"] = f"Error: {str(e)}"
        health_report["status"] = "Error"

    if health_report["status"] == "Error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_report

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "images")

@app.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    minio: Minio = Depends(get_minio),
):
    image_id = uuid4()
    object_name = f"{image_id}/{file.filename}"

    try:
        contents = await file.read()
        from io import BytesIO
        minio.put_object(
            MINIO_BUCKET,
            object_name,
            BytesIO(contents),
            length=len(contents),
            content_type=file.content_type, # type: ignore
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {e}")

    record = Image(
        id=image_id,
        description=description,
        filename=file.filename,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    ocr_result = ocr.run_ocr(contents)
    record.ocr_text = " ".join(ocr_result.get("text", []))
    record.ocr_boxes = [{
        "text": ocr_result["text"][i],
        "left": ocr_result["left"][i],
        "top": ocr_result["top"][i],
        "width": ocr_result["width"][i],
        "height": ocr_result["height"][i],
    } for i in range(len(ocr_result.get("text", []))) if ocr_result["text"][i].strip() != ""]

    db.commit()

    return {"id": str(record.id), "filename": record.filename}

@app.get("/images/")
def list_images(db: Session = Depends(get_db)):
    images = db.query(Image).all()
    return [{"id": str(image.id), "filename": image.filename, "description": image.description} for image in images]

@app.get("/images/{image_id}")
def get_image(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "id": str(image.id),
        "filename": image.filename,
        "description": image.description,
        "ocr_text": image.ocr_text,
        "ocr_boxes": image.ocr_boxes,
    }

@app.get("/images/{id}/file")
def download_image(id: str, db: Session = Depends(get_db), minio: Minio = Depends(get_minio)):
    image = db.query(Image).filter(Image.id == id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    object_name = f"{id}/{image.filename}"
    try:
        response = minio.get_object(MINIO_BUCKET, object_name)
        return Response(content=response.read(), media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO download failed: {e}")