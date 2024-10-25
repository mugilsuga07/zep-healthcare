from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import uuid4

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.schema import BaseNode, MetadataMode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryResult,
)
from llama_index.core.vector_stores.utils import (
    metadata_dict_to_node,
    node_to_metadata_dict,
)
from kb import KB, KBDocs

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PGVectorStore(BasePydanticVectorStore):
    stores_text = True
    flat_metadata = False
    connection_string: str
    async_connection_string: Union[str, sqlalchemy.engine.URL]
    embed_dim: int
    tenant_id: str
    debug = False
    organization_id: Optional[str] = None
    current_user: Optional[str] = None
    _engine: Any = PrivateAttr()
    _session: Any = PrivateAttr()
    _async_engine: Any = PrivateAttr()
    _async_session: Any = PrivateAttr()
    _is_initialized: bool = PrivateAttr(default=False)

    def _connect(self) -> None:
        from sqlalchemy import create_engine

        self._engine = create_engine(self.connection_string, echo=self.debug)
        self._session = sessionmaker(self._engine)

        self._async_engine = create_async_engine(self.async_connection_string)
        self._async_session = sessionmaker(self._async_engine, class_=AsyncSession)

    def _initialize(self) -> None:
        if not self._is_initialized:
            self._connect()
            from sqlalchemy import inspect
            inspector = inspect(self._engine)
            table_names = inspector.get_table_names()
            print(f"Existing tables: {table_names}")
            if 'kbdocs' not in table_names:
                print("Table 'kbdocs' not found, creating it...")
                Base.metadata.create_all(self._engine)
                print("Table 'kbdocs' created.")
            else:
                print("Table 'kbdocs' already exists, not creating it.")
            self._is_initialized = True

    def add(self, nodes: List[BaseNode], kb_metadata: dict, **add_kwargs: Any) -> List[str]:
        self._initialize()
        ids = []

        with self._session() as session:
            existing_kb = session.query(KB).filter_by(
                name=kb_metadata.get("name"),
                tenant_id=self.tenant_id,
                organization_id=self.organization_id
            ).first()

            if existing_kb:
                kb_id = existing_kb.id
            else:
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
                session.add(kb_record)
                session.commit()

        with self._session() as session, session.begin():
            for node in nodes:
                ids.append(node.node_id)
                item = self._node_to_table_row(node, kb_id)
                session.add(item)
            session.commit()
        return ids

    # Implement other necessary methods like async_add, _node_to_table_row, _build_query, etc.

    async def async_add(self, nodes: List[BaseNode], kb_metadata: dict, **kwargs: Any) -> List[str]:
        self._initialize()
        ids = []

        async with self._async_session() as session:
            existing_kb = await session.execute(
                sqlalchemy.select(KB).filter_by(
                    name=kb_metadata.get("name"),
                    tenant_id=self.tenant_id,
                    organization_id=self.organization_id
                )
            )
            existing_kb = existing_kb.scalar()

            if existing_kb:
                kb_id = existing_kb.id
            else:
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
                session.add(kb_record)
                await session.commit()

        async with self._async_session() as session, session.begin():
            for node in nodes:
                ids.append(node.node_id)
                item = self._node_to_table_row(node, kb_id)
                session.add(item)
            await session.commit()
        return ids

    def _node_to_table_row(self, node: BaseNode, kb_id: str) -> Any:
        return KBDocs(
            id=node.node_id,
            kb_id=kb_id,
            embedding=node.get_embedding(),
            title=node.get_content(metadata_mode=MetadataMode.NONE),
            item_metadata=node_to_metadata_dict(
                node,
                remove_text=True,
                flat_metadata=self.flat_metadata,
            ),
            text=node.get_content(),
            created_by=self.current_user,
            last_modified_by=self.current_user,
            organization_id=self.organization_id,
            tenant_id=self.tenant_id,
        )

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
            node = metadata_dict_to_node(row.item_metadata)
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









