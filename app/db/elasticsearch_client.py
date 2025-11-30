"""
Elasticsearch client for full-text search operations.
"""
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch
from app.core.config import settings


class ElasticsearchClient:
    """Async Elasticsearch client for search and indexing."""
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        self.index_name = settings.elasticsearch_index
    
    async def connect(self):
        """Establish connection to Elasticsearch."""
        self.client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            verify_certs=False  # Set to True in production with proper certs
        )
        
        # Check connection
        if await self.client.ping():
            print(f"✅ Connected to Elasticsearch at {settings.elasticsearch_host}:{settings.elasticsearch_port}")
        else:
            raise ConnectionError("Failed to connect to Elasticsearch")
    
    async def disconnect(self):
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            print("✅ Disconnected from Elasticsearch")
    
    async def search(
        self, 
        query: str, 
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Search documents using full-text search.
        
        Args:
            query: Search query string
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Search results with hits and metadata
        """
        if not self.client:
            return {"hits": {"hits": [], "total": {"value": 0}}}
        
        # Build Elasticsearch query
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content", "url"],  # Boost title matches
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "highlight": {
                "fields": {
                    "content": {"fragment_size": 150, "number_of_fragments": 3}
                }
            }
        }
        
        result = await self.client.search(
            index=self.index_name,
            body=search_body,
            size=size,
            from_=from_
        )
        
        return result
    
    async def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Index a single document.
        
        Args:
            doc_id: Unique document ID
            document: Document data to index
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        await self.client.index(
            index=self.index_name,
            id=doc_id,
            document=document
        )
        return True
    
    async def bulk_index(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk index multiple documents for efficiency.
        
        Args:
            documents: List of documents with '_id' field
            
        Returns:
            Bulk operation result
        """
        if not self.client or not documents:
            return {"errors": True, "items": []}
        
        # Build bulk operations
        operations = []
        for doc in documents:
            doc_id = doc.pop('_id', None)
            operations.append({"index": {"_index": self.index_name, "_id": doc_id}})
            operations.append(doc)
        
        result = await self.client.bulk(operations=operations)
        return result
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        if not self.client:
            return None
        
        try:
            result = await self.client.get(index=self.index_name, id=doc_id)
            return result['_source']
        except Exception:
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID."""
        if not self.client:
            return False
        
        try:
            await self.client.delete(index=self.index_name, id=doc_id)
            return True
        except Exception:
            return False
    
    async def create_index(self):
        """Create index with mapping if it doesn't exist."""
        if not self.client:
            return
        
        # Define index mapping
        mapping = {
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "content": {"type": "text", "analyzer": "english"},
                    "domain": {"type": "keyword"},
                    "crawl_date": {"type": "date"},
                    "language": {"type": "keyword"},
                    "metadata": {"type": "object", "enabled": False}
                }
            },
            "settings": {
                "number_of_shards": 5,
                "number_of_replicas": 2
            }
        }
        
        # Create index if it doesn't exist
        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(index=self.index_name, body=mapping)
            print(f"✅ Created Elasticsearch index: {self.index_name}")


# Global Elasticsearch client instance
es_client = ElasticsearchClient()