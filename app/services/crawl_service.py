"""
Crawl service for handling crawl and re-crawl requests.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from app.db.postgres_client import postgres_client
from app.db.rabbitmq_client import rabbitmq_client
from app.models.responses import JobResponse, JobStatusResponse


class CrawlService:
    """Service for managing crawl jobs."""
    
    async def create_recrawl_job(
        self,
        url: str,
        priority: int = 10
    ) -> JobResponse:
        """
        Create a high-priority re-crawl job with 1-hour SLA.
        
        Args:
            url: URL to re-crawl
            priority: Priority level (0-10)
            
        Returns:
            JobResponse with job details
        """
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # SLA: 1 hour from now
        sla_deadline = created_at + timedelta(hours=1)
        
        # Prepare job data
        job_data = {
            'id': job_id,
            'job_type': 'recrawl',
            'url': str(url),  # Convert HttpUrl to string
            'priority': priority,
            'status': 'pending',
            'created_at': created_at,
            'sla_deadline': sla_deadline
        }
        
        # Save to database
        await postgres_client.create_job(job_data)
        
        # Publish to high-priority queue
        queue_data = {
            'job_id': job_id,
            'url': str(url),
            'job_type': 'recrawl',
            'priority': priority,
            'created_at': created_at.isoformat()
        }
        
        rabbitmq_client.publish_recrawl_job(queue_data)
        
        return JobResponse(
            job_id=job_id,
            status='pending',
            message='Re-crawl job created successfully. Will complete within 1 hour.',
            created_at=created_at,
            sla_deadline=sla_deadline
        )
    
    async def create_crawl_job(
        self,
        url: str,
        priority: int = 0
    ) -> JobResponse:
        """
        Create a normal-priority crawl job.
        
        Args:
            url: URL to crawl
            priority: Priority level (0-10)
            
        Returns:
            JobResponse with job details
        """
        job_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Prepare job data
        job_data = {
            'id': job_id,
            'job_type': 'crawl',
            'url': str(url),
            'priority': priority,
            'status': 'pending',
            'created_at': created_at
        }
        
        # Save to database
        await postgres_client.create_job(job_data)
        
        # Publish to normal crawl queue
        queue_data = {
            'job_id': job_id,
            'url': str(url),
            'job_type': 'crawl',
            'priority': priority,
            'created_at': created_at.isoformat()
        }
        
        rabbitmq_client.publish_crawl_job(queue_data)
        
        return JobResponse(
            job_id=job_id,
            status='pending',
            message='Crawl job created successfully',
            created_at=created_at,
            sla_deadline=None
        )
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Get status of a crawl/re-crawl job.
        
        Args:
            job_id: Job ID to query
            
        Returns:
            JobStatusResponse or None if not found
        """
        job_data = await postgres_client.get_job(job_id)
        
        if not job_data:
            return None
        
        # Convert datetime strings back to datetime objects for response
        for date_field in ['created_at', 'started_at', 'completed_at', 'sla_deadline']:
            if job_data.get(date_field):
                if isinstance(job_data[date_field], str):
                    job_data[date_field] = datetime.fromisoformat(job_data[date_field])
        
        return JobStatusResponse(**job_data)
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        **kwargs
    ) -> bool:
        """
        Update job status and other fields.
        
        Args:
            job_id: Job ID
            status: New status
            **kwargs: Additional fields to update
            
        Returns:
            True if successful
        """
        return await postgres_client.update_job_status(job_id, status, **kwargs)


# Global crawl service instance
crawl_service = CrawlService()