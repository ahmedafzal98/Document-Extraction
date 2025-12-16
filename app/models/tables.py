# app/models/tables.py
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    TIMESTAMP,
    Boolean,
    Float,
    func,
    Date
)
from app.db import Base
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    gcs_path = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="processing")

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    extracted_fields = relationship(
        "ExtractedField",
        back_populates="document",
        cascade="all, delete"
    )

    matches = relationship(
        "Match",
        back_populates="document",
        cascade="all, delete"
    )


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )

    field_name = Column(String(100), nullable=False)
    field_value = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="extracted_fields")

class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String, nullable=False)
    dataset_doa = Column(Date, nullable=True)
    dataset_dob = Column(Date, nullable=True)
    dataset_referral = Column(String, nullable=True)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )

    dataset_index = Column(Integer)
    dataset_name = Column(String)
    dataset_doa = Column(String)
    dataset_dob = Column(String)
    dataset_referral = Column(Text)

    extracted_name = Column(String)
    extracted_doa = Column(String)
    extracted_dob = Column(String)
    extracted_referral = Column(Text)

    name_score = Column(Float)
    doa_match = Column(Boolean)
    dob_match = Column(Boolean)
    referral_score = Column(Float)
    referral_match = Column(Boolean)

    match_status = Column(String)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="matches")
