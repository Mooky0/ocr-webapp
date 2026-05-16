import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Generator
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Image, NotificationSubscription
from notification import send_notification

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
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "images")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

logger.info(f"Database URL: {DB_URL}")
logger.info(f"MinIO URL: {MINIO_URL}")
logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    conn.execute(text(
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS ocr_status VARCHAR DEFAULT 'pending'"
    ))
    conn.commit()

minio_client = Minio(
    MINIO_URL.replace("http://", ""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)

kafka_producer: AIOKafkaProducer | None = None


async def consume_ocr_results():
    consumer = AIOKafkaConsumer(
        "ocr-results",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="backend-results-consumer",
        value_deserializer=lambda b: json.loads(b.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("OCR results consumer started")
    try:
        async for msg in consumer:
            result = msg.value
            image_id = result.get("image_id")
            logger.info(f"Received OCR result for image {image_id}")

            db = SessionLocal()
            try:
                image = db.query(Image).filter(Image.id == image_id).first()
                if not image:
                    logger.warning(f"Image {image_id} not found in DB")
                    continue

                if result.get("success"):
                    image.ocr_text = result.get("ocr_text", "")
                    image.ocr_boxes = result.get("ocr_boxes", [])
                    image.ocr_status = "completed"
                else:
                    image.ocr_status = "failed"
                    logger.error(f"OCR failed for {image_id}: {result.get('error')}")

                db.commit()

                # Notify subscribers
                subscribers = db.query(NotificationSubscription).all()
                send_notification(subscribers, image)
            finally:
                db.close()
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.stop()
        logger.info("OCR results consumer stopped")


async def start_producer_with_retry(retries: int = 15, delay: float = 4.0) -> AIOKafkaProducer:
    for attempt in range(retries):
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        try:
            await producer.start()
            logger.info("Kafka producer started")
            return producer
        except Exception as e:
            await producer.stop()
            logger.warning(f"Kafka not ready (attempt {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after retries")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global kafka_producer
    kafka_producer = await start_producer_with_retry()

    consumer_task = asyncio.create_task(consume_ocr_results())

    yield

    consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)
    await kafka_producer.stop()
    logger.info("Kafka producer stopped")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_minio() -> Minio:
    return minio_client


app = FastAPI(lifespan=lifespan)

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


@app.post("/images", status_code=status.HTTP_202_ACCEPTED)
async def upload_image(
    file: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    minio: Minio = Depends(get_minio),
):
    image_id = uuid4()
    object_name = f"{image_id}/{file.filename}"

    contents = await file.read()
    try:
        minio.put_object(
            MINIO_BUCKET,
            object_name,
            BytesIO(contents),
            length=len(contents),
            content_type=file.content_type,  # type: ignore
        )
    except Exception as e:
        logger.exception(f"MinIO upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {e}")

    record = Image(
        id=image_id,
        description=description,
        filename=file.filename,
        ocr_status="pending",
    )
    db.add(record)
    db.commit()

    await kafka_producer.send(  # type: ignore[union-attr]
        "ocr-requests",
        value={
            "image_id": str(image_id),
            "object_name": object_name,
            "description": description,
        },
    )
    logger.info(f"Published OCR request for image {image_id}")

    return {"id": str(image_id), "filename": file.filename, "status": "pending"}


@app.get("/images")
def list_images(db: Session = Depends(get_db)):
    images = db.query(Image).all()
    return [
        {
            "id": str(image.id),
            "filename": image.filename,
            "description": image.description,
            "ocr_status": image.ocr_status,
        }
        for image in images
    ]


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
        "ocr_status": image.ocr_status,
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


@app.post("/subscribe")
def subscribe(email: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(NotificationSubscription).filter(
        NotificationSubscription.email == email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already subscribed")

    subscription = NotificationSubscription(email=email)
    db.add(subscription)
    db.commit()
    return {"message": "Subscribed successfully"}
