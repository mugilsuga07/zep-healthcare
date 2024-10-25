from hpi_summarizer import HPISummarizer
from pgvector_store import PGVectorStore

if __name__ == "__main__":
    pg_vector_store = PGVectorStore(
        connection_string="postgresql+psycopg2://postgres:charizards@localhost:5435/jhm_vectordb",
        async_connection_string="postgresql+asyncpg://postgres:charizards@localhost:5435/jhm_vectordb",
        embed_dim=1536,
        tenant_id=None,
        organization_id=None,
        current_user=None,
        debug=True
    )
    hpi_summarizer = HPISummarizer(store=pg_vector_store)
    conversation = "Example conversation text here."
    summary = hpi_summarizer.summarize(conversation)
    print(summary)
    hpi_summarizer.store_hpi(conversation, summary)





































