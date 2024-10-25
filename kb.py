
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class KB(Base):
    __tablename__ = "kb"
    id = Column(UUID, primary_key=True)
    name = Column(String(1024))
    data_type = Column(String(24))
    metadata_ = Column("metadata", JSONB)
    status = Column(String(24))
    created_by = Column(UUID)
    created_date = Column(TIMESTAMP(timezone=True))
    last_modified_by = Column(UUID)
    last_modified_date = Column(TIMESTAMP(timezone=True))
    is_deleted = Column(Boolean, default=False)
    organization_id = Column(UUID, nullable=True)
    object_acl = Column(JSONB, nullable=True)
    tenant_id = Column(UUID, default=None)

class KBDocs(Base):
    __tablename__ = "kb_docs"
    id = Column(UUID, primary_key=True)
    kb_id = Column(UUID, ForeignKey('kb.id'), nullable=False)
    title = Column(String, nullable=False)
    item_metadata=Column("item_metadata", JSONB)
    text = Column(String, nullable=True)
    url = Column(String, nullable=True)
    tokens = Column(Integer, nullable=True)
    embedding = Column(Vector(1536))
    created_by = Column(UUID)
    created_date = Column(TIMESTAMP(timezone=True))
    last_modified_by = Column(UUID)
    last_modified_date = Column(TIMESTAMP(timezone=True))
    is_deleted = Column(Boolean, default=False)
    organization_id = Column(UUID, nullable=True)
    object_acl = Column(JSONB, nullable=True)
    tenant_id = Column(UUID, default=None)