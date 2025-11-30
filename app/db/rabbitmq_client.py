"""
RabbitMQ client for managing crawl job queues.
"""
import json
import pika
from typing import Dict, Any, Optional, Callable
from app.core.config import settings


class RabbitMQClient:
    """RabbitMQ client for job queue management."""
    
    def __init__(self):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        # Parse connection parameters
        params = pika.URLParameters(settings.rabbitmq_url)
        
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        
        # Declare queues
        self._declare_queues()
        
        print(f"✅ Connected to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}")
    
    def disconnect(self):
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("✅ Disconnected from RabbitMQ")
    
    def _declare_queues(self):
        """Declare all necessary queues."""
        # Crawl queue (normal priority)
        self.channel.queue_declare(
            queue=settings.rabbitmq_crawl_queue,
            durable=True,  # Survives broker restart
            arguments={
                'x-max-priority': 10  # Enable priority queue
            }
        )
        
        # Re-crawl queue (high priority)
        self.channel.queue_declare(
            queue=settings.rabbitmq_recrawl_queue,
            durable=True,
            arguments={
                'x-max-priority': 10
            }
        )
    
    def publish_job(
        self, 
        queue_name: str,
        job_data: Dict[str, Any],
        priority: int = 0
    ) -> bool:
        """
        Publish a job to the queue.
        
        Args:
            queue_name: Queue to publish to
            job_data: Job information
            priority: Job priority (0-10, higher = more important)
            
        Returns:
            True if successful
        """
        if not self.channel:
            return False
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(job_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    priority=priority
                )
            )
            return True
        except Exception as e:
            print(f"❌ Failed to publish job: {e}")
            return False
    
    def publish_crawl_job(self, job_data: Dict[str, Any]) -> bool:
        """Publish to normal crawl queue."""
        return self.publish_job(
            settings.rabbitmq_crawl_queue,
            job_data,
            priority=0
        )
    
    def publish_recrawl_job(self, job_data: Dict[str, Any]) -> bool:
        """Publish to high-priority re-crawl queue."""
        return self.publish_job(
            settings.rabbitmq_recrawl_queue,
            job_data,
            priority=10  # Highest priority
        )
    
    def consume_jobs(
        self, 
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False
    ):
        """
        Start consuming jobs from queue.
        
        Args:
            queue_name: Queue to consume from
            callback: Function to process each message
            auto_ack: Auto-acknowledge messages
        """
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")
        
        self.channel.basic_qos(prefetch_count=1)  # Fair dispatch
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=auto_ack
        )
        
        print(f"📥 Started consuming from queue: {queue_name}")
        self.channel.start_consuming()
    
    def acknowledge_job(self, delivery_tag):
        """Acknowledge a job as completed."""
        if self.channel:
            self.channel.basic_ack(delivery_tag=delivery_tag)
    
    def reject_job(self, delivery_tag, requeue: bool = True):
        """Reject a job (optionally requeue it)."""
        if self.channel:
            self.channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
    
    def get_queue_size(self, queue_name: str) -> int:
        """Get number of messages in queue."""
        if not self.channel:
            return 0
        
        method = self.channel.queue_declare(
            queue=queue_name,
            durable=True,
            passive=True  # Don't create, just get info
        )
        return method.method.message_count


# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()