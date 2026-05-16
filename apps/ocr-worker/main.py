import io
import json
import logging
import os
import time

from kafka import KafkaConsumer, KafkaProducer
from minio import Minio
from PIL import Image as PILImage
import pytesseract
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MINIO_URL = os.getenv("MINIO_URL", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "password")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "images")


def wait_for_kafka(servers: str, retries: int = 10, delay: int = 5):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(bootstrap_servers=servers)
            producer.close()
            logger.info("Kafka is ready")
            return
        except Exception as e:
            logger.warning(f"Kafka not ready (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after retries")


def run_ocr(image_bytes: bytes) -> dict:
    img = PILImage.open(io.BytesIO(image_bytes))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    return data


def main():
    wait_for_kafka(KAFKA_BOOTSTRAP_SERVERS)

    minio_client = Minio(
        MINIO_URL.replace("http://", ""),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    consumer = KafkaConsumer(
        "ocr-requests",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="ocr-worker-group",
        value_deserializer=lambda b: json.loads(b.decode()),
        auto_offset_reset="earliest",
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode(),
    )

    logger.info("OCR worker started, waiting for messages...")

    for msg in consumer:
        request = msg.value
        image_id = request.get("image_id")
        object_name = request.get("object_name")
        logger.info(f"Processing OCR request for image {image_id}")

        try:
            response = minio_client.get_object(MINIO_BUCKET, object_name)
            image_bytes = response.read()

            ocr_data = run_ocr(image_bytes)

            ocr_text = " ".join(
                word for word in ocr_data.get("text", []) if word.strip()
            )
            ocr_boxes = [
                {
                    "text": ocr_data["text"][i],
                    "left": ocr_data["left"][i],
                    "top": ocr_data["top"][i],
                    "width": ocr_data["width"][i],
                    "height": ocr_data["height"][i],
                }
                for i in range(len(ocr_data.get("text", [])))
                if ocr_data["text"][i].strip()
            ]

            producer.send(
                "ocr-results",
                value={
                    "image_id": image_id,
                    "ocr_text": ocr_text,
                    "ocr_boxes": ocr_boxes,
                    "success": True,
                    "error": None,
                },
            )
            producer.flush()
            logger.info(f"OCR complete for image {image_id}, found {len(ocr_boxes)} words")

        except Exception as e:
            logger.exception(f"OCR failed for image {image_id}: {e}")
            producer.send(
                "ocr-results",
                value={
                    "image_id": image_id,
                    "ocr_text": None,
                    "ocr_boxes": None,
                    "success": False,
                    "error": str(e),
                },
            )
            producer.flush()


if __name__ == "__main__":
    main()
