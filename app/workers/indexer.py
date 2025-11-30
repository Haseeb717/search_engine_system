"""
Indexer worker for building the inverted index in Elasticsearch.
Takes processed content and indexes it for fast searching.
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import hashlib

from app.db.elasticsearch_client import es_client
from app.db.postgres_client import postgres_client


class IndexerWorker:
    """Worker that indexes processed content into Elasticsearch."""
    
    def __init__(self):
        self.batch_size = 100  # Batch documents for bulk indexing
        self.batch = []
    
    def generate_document_id(self, url: str) -> str:
        """
        Generate a unique document ID from URL.
        
        Args:
            url: Page URL
            
        Returns:
            Unique document ID
        """
        return hashlib.sha256(url.encode()).hexdigest()
    
    async def index_document(self, processed_data: Dict[str, Any]) -> bool:
        """
        Index a single processed document into Elasticsearch.
        
        Args:
            processed_data: Processed page data
            
        Returns:
            True if successful
        """
        try:
            # Generate unique document ID
            doc_id = self.generate_document_id(processed_data['url'])
            
            # Prepare document for Elasticsearch
            # Note: We don't store all tokens in ES, just the content
            # Elasticsearch will tokenize and index it automatically
            es_document = {
                'url': processed_data['url'],
                'title': processed_data['title'],
                'content': processed_data['content'],  # ES will tokenize this
                'domain': processed_data['domain'],
                'crawl_date': processed_data['crawl_date'],
                'keywords': processed_data.get('keywords', []),
                'metadata': {
                    'token_count': processed_data.get('token_count', 0),
                    'content_hash': str(processed_data.get('content_hash', ''))
                }
            }
            
            # Index into Elasticsearch
            success = await es_client.index_document(doc_id, es_document)
            
            if success:
                print(f"✅ Indexed document: {processed_data['url']}")
                
                # Save metadata to PostgreSQL
                await self._save_metadata(doc_id, processed_data)
            
            return success
            
        except Exception as e:
            print(f"❌ Error indexing document: {e}")
            return False
    
    async def bulk_index(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk index multiple documents for better performance.
        
        Args:
            documents: List of processed documents
            
        Returns:
            Bulk operation result
        """
        try:
            # Prepare bulk documents
            bulk_docs = []
            
            for doc in documents:
                doc_id = self.generate_document_id(doc['url'])
                
                es_document = {
                    '_id': doc_id,
                    'url': doc['url'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'domain': doc['domain'],
                    'crawl_date': doc['crawl_date'],
                    'keywords': doc.get('keywords', []),
                    'metadata': {
                        'token_count': doc.get('token_count', 0),
                        'content_hash': str(doc.get('content_hash', ''))
                    }
                }
                
                bulk_docs.append(es_document)
            
            # Bulk index
            result = await es_client.bulk_index(bulk_docs)
            
            print(f"✅ Bulk indexed {len(documents)} documents")
            
            # Save all metadata
            for doc in documents:
                doc_id = self.generate_document_id(doc['url'])
                await self._save_metadata(doc_id, doc)
            
            return result
            
        except Exception as e:
            print(f"❌ Error in bulk indexing: {e}")
            return {'errors': True, 'items': []}
    
    async def _save_metadata(self, doc_id: str, processed_data: Dict[str, Any]):
        """
        Save document metadata to PostgreSQL.
        
        Args:
            doc_id: Document ID
            processed_data: Processed document data
        """
        try:
            url_hash = hashlib.sha256(processed_data['url'].encode()).hexdigest()
            
            metadata = {
                'url': processed_data['url'],
                'url_hash': url_hash,
                'domain': processed_data['domain'],
                'title': processed_data['title'],
                'crawl_date': datetime.utcnow(),
                'http_status_code': 200,  # Assuming success
                'content_hash': str(processed_data.get('content_hash', ''))
            }
            
            await postgres_client.save_document_metadata(metadata)
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to save metadata: {e}")
    
    async def process_and_index(
        self, 
        job_id: str, 
        processed_data: Dict[str, Any]
    ) -> bool:
        """
        Process a job and index the document.
        
        Args:
            job_id: Job ID
            processed_data: Processed page data
            
        Returns:
            True if successful
        """
        print(f"📥 Indexing job {job_id}")
        
        # Index the document
        success = await self.index_document(processed_data)
        
        if success:
            # Update job status to completed
            await postgres_client.update_job_status(
                job_id,
                status='completed',
                completed_at=datetime.utcnow(),
                result={
                    'indexed': True,
                    'document_id': self.generate_document_id(processed_data['url']),
                    'token_count': processed_data.get('token_count', 0)
                }
            )
            print(f"✅ Job {job_id} completed successfully")
            return True
        else:
            # Update job as failed
            await postgres_client.update_job_status(
                job_id,
                status='failed',
                completed_at=datetime.utcnow(),
                error='Failed to index document'
            )
            print(f"❌ Job {job_id} failed")
            return False
    
    async def start(self):
        """
        Start the indexer worker.
        In a real system, this would consume from a processing queue.
        """
        print("🚀 Starting indexer worker...")
        
        # Connect to services
        await es_client.connect()
        await es_client.create_index()
        await postgres_client.connect()
        
        print("✅ Indexer worker ready")
        
        # In production, this would consume from a queue
        # For now, it's just a placeholder


async def main():
    """Main entry point for indexer worker."""
    worker = IndexerWorker()
    await worker.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping indexer worker...")
        await es_client.disconnect()
        await postgres_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())