

from typing import List, Union
from database.db import database
from langchain.vectorstores import Weaviate
from sentence_transformers import SentenceTransformer

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()

key = os.getenv('KEY')
        
class STretriever(BaseRetriever):
    """Retriever that aggregates hotel and tour documents for itinerary generation."""

    vectorstore_hotels: Weaviate
    vectorstore_tours: Weaviate
    embedding_model: SentenceTransformer
    k: int = 3

    async def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        # Delegate to async implementation
        return await self._aget_relevant_documents(query, run_manager=run_manager)
    
    
    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        print("query _get_relevant_documents", query)
        convesation_id = query.split(key)[1]
        query_find = f"SELECT * FROM conversations WHERE id={convesation_id}"
        results = await database.fetch_all(query=query_find)
        agentid = dict(results[0])["agentid"]
        query_after = query.split(key)[0]
        print("query _get_relevant_documents query_after ", query_after)
        
        # Run CPU-intensive encoding in threadpool
        query_vector = await asyncio.get_event_loop().run_in_executor(
            None, 
            self.embedding_model.encode,
            query_after
        )
        query_vector = query_vector.tolist()

        # Query from monetizable classes: hotels and tours
        all_docs = []
        
        where_filter_agent = {
            "path": "agentId",
            "operator": "Equal",
            "valueString": agentid
        }
        
        # Query from hotels (no agentId filter needed, hotels are global) - skip if class doesn't exist
        try:
            docs_hotels = self.vectorstore_hotels.similarity_search_by_vector(
                embedding=query_vector,
                k=self.k,
                where_filter=where_filter_agent
            )
            all_docs.extend(docs_hotels)
            print(f"✓ Retrieved {len(docs_hotels)} documents from hotels")
        except Exception as e:
            print(f"⚠ Warning: Could not query hotels class: {str(e)}")
            # Continue with other classes
        
        # Query from tours (no agentId filter needed, tours are global) - skip if class doesn't exist
        try:
            docs_tours = self.vectorstore_tours.similarity_search_by_vector(
                embedding=query_vector,
                k=self.k,
                where_filter=where_filter_agent
            )
            all_docs.extend(docs_tours)
            print(f"✓ Retrieved {len(docs_tours)} documents from tours")
        except Exception as e:
            print(f"⚠ Warning: Could not query tours class: {str(e)}")
            # Continue with other classes
        
        # Remove duplicates based on content and return top k
        seen_contents = set()
        unique_docs = []
        for doc in all_docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_docs.append(doc)
            if len(unique_docs) >= self.k:
                break
        
        return unique_docs[:self.k]

    # Optional: Provide a more efficient native implementation by overriding
    # _aget_relevant_documents
    # async def _aget_relevant_documents(
    #     self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    # ) -> List[Document]:
    #     """Asynchronously get documents relevant to a query.

    #     Args:
    #         query: String to find relevant documents for
    #         run_manager: The callbacks handler to use

    #     Returns:
    #         List of relevant documents
    #     """

