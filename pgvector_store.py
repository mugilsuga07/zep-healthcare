from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import uuid4

import sqlalchemy
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

class MetadataFilters:
    pass

class BaseNode:
    def get_embedding(self):
        return [0.0] * 1536

    def get_content(self, metadata_mode=None):
        return "content"

    def set_content(self, content):
        pass

    def node_id(self):
        return str(uuid4())

class VectorStoreQuery:
    def __init__(self):
        self.query_embedding = None
        self.similarity_top_k = 10
        self.filters = None

class VectorStoreQueryResult:
    def __init__(self, nodes, similarities, ids):
        self.nodes = nodes
        self.similarities = similarities
        self.ids = ids

Base = declarative_base()

class KB(Base):
    __tablename__ = "kb"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(1024))
    data_type = Column(String(24))
    metadata_ = Column("metadata", JSONB)
    status = Column(String(24))
    created_by = Column(UUID(as_uuid=True))
    created_date = Column(TIMESTAMP(timezone=True))
    last_modified_by = Column(UUID(as_uuid=True))
    last_modified_date = Column(TIMESTAMP(timezone=True))
    is_deleted = Column(Boolean, default=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    object_acl = Column(JSONB, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), default=None)

class KBDocs(Base):
    __tablename__ = "kb_docs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    kb_id = Column(UUID(as_uuid=True), ForeignKey('kb.id'), nullable=False)
    title = Column(String, nullable=False)
    item_metadata = Column("item_metadata", JSONB)
    text = Column(String, nullable=True)
    url = Column(String, nullable=True)
    tokens = Column(Integer, nullable=True)
    embedding = Column(Vector(1536))
    created_by = Column(UUID(as_uuid=True))
    created_date = Column(TIMESTAMP(timezone=True))
    last_modified_by = Column(UUID(as_uuid=True))
    last_modified_date = Column(TIMESTAMP(timezone=True))
    is_deleted = Column(Boolean, default=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    object_acl = Column(JSONB, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), default=None)

class PGVectorStore:
    stores_text = True
    flat_metadata = False

    def __init__(
        self,
        connection_string: Union[str, sqlalchemy.engine.URL],
        async_connection_string: Union[str, sqlalchemy.engine.URL],
        embed_dim: int = 1536,
        tenant_id: str = "",
        organization_id: Optional[str] = None,
        current_user: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        self.connection_string = connection_string
        self.async_connection_string = async_connection_string
        self.embed_dim = embed_dim
        self.tenant_id = tenant_id
        self.organization_id = organization_id
        self.current_user = current_user
        self.debug = debug
        self._is_initialized = False

    async def async_close(self) -> None:
        if not self._is_initialized:
            return
        await self._async_engine.dispose()

    def _connect(self) -> None:
        from sqlalchemy import create_engine

        self._engine = create_engine(self.connection_string, echo=self.debug)
        self._session = sessionmaker(self._engine)

        self._async_engine = create_async_engine(self.async_connection_string)
        self._async_session = sessionmaker(self._async_engine, class_=AsyncSession)

    def _initialize(self) -> None:
        if not self._is_initialized:
            self._connect()
            self._is_initialized = True

    @property
    def client(self) -> Any:
        if not self._is_initialized:
            self._initialize()
        return self._engine

    def _node_to_table_row(self, node: BaseNode, kb_id: str) -> Any:
        return KBDocs(
            id=node.node_id(),
            kb_id=kb_id,
            embedding=node.get_embedding(),
            title=node.get_content(),
            item_metadata={},  # Replace with actual metadata conversion
            text=node.get_content(),
            created_by=self.current_user,
            last_modified_by=self.current_user,
            organization_id=self.organization_id,
            tenant_id=self.tenant_id,
        )

    def add(self, nodes: List[BaseNode], kb_metadata: dict, **add_kwargs: Any) -> List[str]:
        self._initialize()
        ids = []
        kb_id = str(uuid4())

        kb_record = KB(
            id=kb_id,
            name=kb_metadata.get("name"),
            data_type=kb_metadata.get("data_type"),
            metadata=kb_metadata.get("metadata"),
            status=kb_metadata.get("status"),
            created_by=self.current_user,
            created_date=datetime.now(),
            last_modified_by=self.current_user,
            last_modified_date=datetime.now(),
            organization_id=self.organization_id,
            tenant_id=self.tenant_id
        )

        with self._session() as session, session.begin():
            session.add(kb_record)
            for node in nodes:
                ids.append(node.node_id())
                item = self._node_to_table_row(node, kb_id)
                session.add(item)
            session.commit()
        return ids

    async def async_add(self, nodes: List[BaseNode], kb_metadata: dict, **kwargs: Any) -> List[str]:
        self._initialize()
        ids = []
        kb_id = str(uuid4())

        kb_record = KB(
            id=kb_id,
            name=kb_metadata.get("name"),
            data_type=kb_metadata.get("data_type"),
            metadata=kb_metadata.get("metadata"),
            status=kb_metadata.get("status"),
            created_by=self.current_user,
            created_date=datetime.now(),
            last_modified_by=self.current_user,
            last_modified_date=datetime.now(),
            organization_id=self.organization_id,
            tenant_id=self.tenant_id
        )

        async with self._async_session() as session, session.begin():
            session.add(kb_record)
            for node in nodes:
                ids.append(node.node_id())
                item = self._node_to_table_row(node, kb_id)
                session.add(item)
            await session.commit()
        return ids

    def _build_query(
        self,
        embedding: Optional[List[float]],
        limit: int = 10,
        metadata_filters: Optional[MetadataFilters] = None,
    ) -> Any:
        from sqlalchemy import select, text

        stmt = select(
            KBDocs.id,
            KBDocs.title,
            KBDocs.item_metadata,
            KBDocs.embedding.cosine_distance(embedding).label("distance"),
        ).order_by(text("distance asc"))

        return stmt.limit(limit)

    def _query_with_score(
        self,
        embedding: Optional[List[float]],
        limit: int = 10,
        metadata_filters: Optional[MetadataFilters] = None,
        **kwargs: Any,
    ) -> List[KBDocs]:
        stmt = self._build_query(embedding, limit, metadata_filters)
        with self._session() as session, session.begin():
            res = session.execute(stmt)
            return res.all()

    async def _aquery_with_score(
        self,
        embedding: Optional[List[float]],
        limit: int = 10,
        metadata_filters: Optional[MetadataFilters] = None,
        **kwargs: Any,
    ) -> List[KBDocs]:
        stmt = self._build_query(embedding, limit, metadata_filters)
        async with self._async_session() as async_session, async_session.begin():
            res = await async_session.execute(stmt)
            return res.all()

    def _db_rows_to_query_result(
        self, rows: List[KBDocs]
    ) -> VectorStoreQueryResult:
        nodes = []
        similarities = []
        ids = []
        for row in rows:
            node = BaseNode()  # Replace with actual node construction
            node.set_content(row.title)
            similarities.append(row.distance)
            ids.append(row.id)
            nodes.append(node)

        return VectorStoreQueryResult(
            nodes=nodes,
            similarities=similarities,
            ids=ids,
        )

    async def aquery(
        self, query: VectorStoreQuery, **kwargs: Any
    ) -> VectorStoreQueryResult:
        self._initialize()
        results = await self._aquery_with_score(
            query.query_embedding,
            query.similarity_top_k,
            query.filters,
            **kwargs,
        )
        return self._db_rows_to_query_result(results)

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        self._initialize()
        results = self._query_with_score(
            query.query_embedding,
            query.similarity_top_k,
            query.filters,
            **kwargs,
        )
        return self._db_rows_to_query_result(results)

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        from sqlalchemy import delete

        self._initialize()
        with self._session() as session, session.begin():
            stmt = delete(KBDocs).where(KBDocs.id == ref_doc_id)
            session.execute(stmt)
            session.commit()

    def retrieve_documents(self, conversation):
        query = VectorStoreQuery()
        result = self.query(query)
        return result.nodes

    async def async_retrieve_documents(self, conversation):
        query = VectorStoreQuery()
        result = await self.aquery(query)
        return result.nodes

from custom_document import Document

def _node_to_table_row(self, node: Document, kb_id: str) -> Any:
    return KBDocs(
        id=node.node_id(),
        kb_id=kb_id,
        embedding=node.get_embedding(),
        title=node.get_content(),
        item_metadata=node.get_metadata(),
        created_by=self.current_user,
        last_modified_by=self.current_user,
        organization_id=self.organization_id,
        tenant_id=self.tenant_id,
    )




    









