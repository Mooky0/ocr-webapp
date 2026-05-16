import uuid

from sqlalchemy import String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    description: Mapped[str] = mapped_column(String)
    filename: Mapped[str] = mapped_column(String)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_boxes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String, unique=True)