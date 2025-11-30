"""
Crawler worker for downloading web pages from the queue.
This worker picks jobs from RabbitMQ and fetches web pages.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.db.rabbitmq_client import rabbitmq_client
from app.db.postgres_client import postgres_client


class CrawlerWorker:
    """Worker that fetches web pages from URLs in the queue."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.crawl_timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'SearchEngineBot/1.0 (+https://example.com/bot)'
            }
        )
    
    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """
        Fetch a web page and extract content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with page content and metadata
        """
        try:
            # Download the page
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract title
            title = soup.title.string if soup.title else "No title"
            
            # Extract main content (remove scripts, styles, etc.)
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            content = soup.get_text(separator=' ', strip=True)
            
            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'domain': domain,
                'status_code': response.status_code,
                'content_length': len(content),
                'crawl_date': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e),
                'crawl_date': datetime.utcnow().isoformat()
            }
    
    async def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single crawl job.
        
        Args:
            job_data: Job information from queue
            
        Returns:
            Result data
        """
        job_id = job_data['job_id']
        url = job_data['url']
        
        print(f"📥 Processing job {job_id}: {url}")
        
        # Update job status to processing
        await postgres_client.update_job_status(
            job_id,
            status='processing',
            started_at=datetime.utcnow()
        )
        
        # Fetch the page
        result = await self.fetch_page(url)
        
        if result['success']:
            # Success - return for further processing
            print(f"✅ Successfully crawled: {url}")
            return {
                'job_id': job_id,
                'page_data': result,
                'status': 'completed'
            }
        else:
            # Failed
            print(f"❌ Failed to crawl {url}: {result.get('error')}")
            
            # Update job as failed
            await postgres_client.update_job_status(
                job_id,
                status='failed',
                completed_at=datetime.utcnow(),
                error=result.get('error')
            )
            
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': result.get('error')
            }
    
    def callback(self, ch, method, properties, body):
        """
        Callback function for RabbitMQ consumer.
        Runs in sync context, so we use asyncio.run() for async operations.
        """
        try:
            # Parse job data
            job_data = json.loads(body)
            
            # Process the job (run async function in sync context)
            result = asyncio.run(self.process_job(job_data))
            
            if result['status'] == 'completed':
                # Send to next stage (processor) via a new queue or direct call
                # For now, we'll just acknowledge
                print(f"✅ Job {result['job_id']} completed")
            
            # Acknowledge the message
            rabbitmq_client.acknowledge_job(method.delivery_tag)
            
        except Exception as e:
            print(f"❌ Error processing job: {e}")
            # Reject and requeue the job
            rabbitmq_client.reject_job(method.delivery_tag, requeue=True)
    
    async def start(self, queue_name: str = None):
        """
        Start consuming jobs from the queue.
        
        Args:
            queue_name: Queue to consume from (default: crawl_queue)
        """
        queue_name = queue_name or settings.rabbitmq_crawl_queue
        
        print(f"🚀 Starting crawler worker on queue: {queue_name}")
        
        # Connect to PostgreSQL
        await postgres_client.connect()
        
        # Start consuming from RabbitMQ
        try:
            rabbitmq_client.consume_jobs(
                queue_name=queue_name,
                callback=self.callback
            )
        except KeyboardInterrupt:
            print("\n🛑 Stopping crawler worker...")
        finally:
            await self.client.aclose()
            await postgres_client.disconnect()


async def main():
    """Main entry point for crawler worker."""
    # Connect to RabbitMQ
    rabbitmq_client.connect()
    
    # Create and start worker
    worker = CrawlerWorker()
    
    # For re-crawl jobs, use the recrawl queue
    # await worker.start(settings.rabbitmq_recrawl_queue)
    
    # For normal crawls
    await worker.start(settings.rabbitmq_crawl_queue)


if __name__ == "__main__":
    asyncio.run(main())