from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import uuid4

import sqlalchemy
import sqlalchemy.ext.asyncio
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
        super().__init__(
            connection_string=connection_string,
            async_connection_string=async_connection_string,
            embed_dim=embed_dim,
            tenant_id=tenant_id,
            organization_id=organization_id,
            current_user=current_user,
            debug=debug,
        )
        self.debug = debug
        self.tenant_id = tenant_id
        self.organization_id = organization_id
        self.current_user = current_user

    async def close(self) -> None:
        if not self._is_initialized:
            return

        self._session.close_all()
        self._engine.dispose()

        await self._async_engine.dispose()

    @classmethod
    def class_name(cls) -> str:
        return "PGVectorStore"

    @classmethod
    def from_params(
        cls,
        host: Optional[str] = None,
        port: Optional[str] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        connection_string: Optional[Union[str, sqlalchemy.engine.URL]] = None,
        async_connection_string: Optional[Union[str, sqlalchemy.engine.URL]] = None,
        embed_dim: int = 1536,
        tenant_id: str = None,
        organization_id: Optional[str] = None,
        current_user: Optional[str] = None,
        debug: bool = False,
    ) -> "PGVectorStore":
        conn_str = (
            connection_string
            or f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        )
        async_conn_str = async_connection_string or (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        )
        return cls(
            connection_string=conn_str,
            async_connection_string=async_conn_str,
            embed_dim=embed_dim,
            tenant_id=tenant_id,
            organization_id=organization_id,
            current_user=current_user,
            debug=debug,
        )

    def _connect(self) -> None:
        from sqlalchemy import create_engine

        self._engine = create_engine(self.connection_string, echo=self.debug)
        self._session = sessionmaker(self._engine)

        self._async_engine = create_async_engine(self.async_connection_string)
        self._async_session = sessionmaker(self._async_engine, class_=AsyncSession)

    def _initialize(self) -> None:
      if not self._is_initialized:
        self._connect()
        # Check if the table exists, and create it if it doesn't
        from sqlalchemy import inspect
        inspector = inspect(self._engine)
        if 'kbdocs' not in inspector.get_table_names():
            Base.metadata.create_all(self._engine)
        self._is_initialized = True



    @property
    def client(self) -> Any:
        if not self._is_initialized:
            self._initialize()
        return self._engine

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

    def add(self, nodes: List[BaseNode], kb_metadata: dict, **add_kwargs: Any) -> List[str]:
        self._initialize()
        ids = []
        kb_id = str(uuid4())
        
        # Insert metadata into KB table
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
                ids.append(node.node_id)
                item = self._node_to_table_row(node, kb_id)
                session.add(item)
            session.commit()
        return ids

    async def async_add(self, nodes: List[BaseNode], kb_metadata: dict, **kwargs: Any) -> List[str]:
        self._initialize()
        ids = []
        kb_id = str(uuid4())
        
        # Insert metadata into KB table
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
                ids.append(node.node_id)
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

# New concrete node implementation
class ConcreteNode(BaseNode):
    def __init__(self, node_id: str, content: str):
        self.node_id = node_id
        self.content = content

    def get_content(self, metadata_mode: MetadataMode = MetadataMode.NONE) -> str:
        return self.content

    def get_metadata_str(self) -> str:
        return ""

    def get_type(self) -> str:
        return "concrete"

    def set_content(self, content: str) -> None:
        self.content = content

    def get_embedding(self) -> List[float]:
        return []

# Main script to test the PGVectorStore and ConcreteNode
def main():
    # Update the connection string with your actual database credentials
    connection_string = "postgresql+psycopg2://postgres:charizards@localhost:5435/jhm_vectordb"
    async_connection_string = "postgresql+asyncpg://postgres:charizards@localhost:5435/jhm_vectordb"
    
    # Initialize the PGVectorStore
    vector_store = PGVectorStore(
        connection_string=connection_string,
        async_connection_string=async_connection_string,
        embed_dim=1536,
        tenant_id="example_tenant",
        organization_id="example_org",
        current_user="example_user",
        debug=True,
    )

    # Create some example nodes
    nodes = [
        ConcreteNode(node_id="1", content="Example content 1"),
        ConcreteNode(node_id="2", content="Example content 2"),
    ]

    # Add data to the store
    metadata = {
        "name": "Example KB",
        "data_type": "text",
        "metadata": {},
        "status": "active"
    }
    vector_store.add(nodes, metadata)

    # Example query
    query = VectorStoreQuery(query_embedding=[0.1, 0.2, 0.3], similarity_top_k=5)
    result = vector_store.query(query)

    # Process the result
    for node in result.nodes:
        print(f"Retrieved node: {node}")

if __name__ == "__main__":
    main()













