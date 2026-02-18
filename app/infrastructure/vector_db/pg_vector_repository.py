import asyncpg
from typing import List, Dict, Optional, Tuple

class PgVectorRepository:

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def add_document(
        self,
        document_key: str,
        user_id: str,
        company_id: str,
        content: str,
        embedding: List[float],
    ):
        """Adds or updates a document embedding."""
        query = """
        INSERT INTO embeddings
        (document_key, user_id, company_id, content, embedding)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            deleted = FALSE
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                document_key,
                user_id,
                company_id,
                content,
                embedding,
            )

    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        company_id: str,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[str, float, Dict]]:
        """
        Uses the match_embeddings RPC function for multi-tenant search.
        Note: This specific method is kept for asyncpg compatibility if needed, 
        but RPC is preferred via Supabase client.
        """
        query = """
        SELECT * FROM match_embeddings($1, $2, $3, $4, $5)
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query,
                list(query_embedding),
                threshold,
                top_k,
                user_id,
                company_id
            )

        return [
            (
                r["document_key"],
                float(r["similarity"]),
                {
                    "content": r["content"],
                    "user_id": r["user_id"],
                    "company_id": r["company_id"],
                },
            )
            for r in rows
        ]

    async def delete_document(self, document_key: str, user_id: str, company_id: str):
        """Soft deletes a document."""
        query = """
        UPDATE embeddings
        SET deleted = TRUE
        WHERE document_key = $1 AND user_id = $2 AND company_id = $3
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, document_key, user_id, company_id)

    async def soft_delete_by_company(self, user_id: str, company_id: str) -> int:
        query = """
        UPDATE embeddings
        SET deleted = TRUE
        WHERE user_id = $1 AND company_id = $2
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, user_id, company_id)
        return int(result.split()[-1])
