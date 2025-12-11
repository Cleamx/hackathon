from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    description = Column(String, nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default=ProcessingStatus.PENDING.value)

    # Path to original file
    file_path = Column(String)

    # Extracted content (legacy - première page uniquement maintenant)
    extracted_text = Column(Text, nullable=True)

    # Pages extraites (JSON: {"0": "html...", "1": "html...", ...})
    extracted_pages = Column(JSON, nullable=True, default=dict)

    # Nombre total de pages
    page_count = Column(Integer, nullable=True)

    # Metadata
    language = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
