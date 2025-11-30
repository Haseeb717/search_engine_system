"""
PostgreSQL client for storing metadata and job status.
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, select
from datetime import datetime
from app.core.config import settings

# Base for SQLAlchemy models
Base = declarative_base()


class CrawlJob(Base):  # type: ignore[valid-type,misc]
    """Model for crawl jobs."""
    __tablename__ = "crawl_jobs"
    
    id = Column(String(36), primary_key=True)  # UUID
    job_type = Column(String(20), nullable=False)  # 'crawl' or 'recrawl'
    url = Column(Text, nullable=False)
    priority = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)


class Document(Base):  # type: ignore[valid-type,misc]
    """Model for document metadata."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False)
    url_hash = Column(String(64), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    title = Column(Text, nullable=True)
    crawl_date = Column(DateTime, default=datetime.utcnow, index=True)
    last_modified = Column(DateTime, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)


class PostgresClient:
    """Async PostgreSQL client wrapper."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
    
    async def connect(self):
        """Establish connection to PostgreSQL."""
        # Use asyncpg driver for async operations
        db_url = settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.engine = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_size=20,
            max_overflow=0
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables if they don't exist
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print(f"✅ Connected to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}")
    
    async def disconnect(self):
        """Close PostgreSQL connection."""
        if self.engine:
            await self.engine.dispose()
            print("✅ Disconnected from PostgreSQL")
    
    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self.session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.session_factory()  # type: ignore[no-any-return]
    
    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a new crawl job.
        
        Args:
            job_data: Job information
            
        Returns:
            Job ID
        """
        async with self.get_session() as session:
            job = CrawlJob(**job_data)
            session.add(job)
            await session.commit()
            return str(job.id)
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        async with self.get_session() as session:
            result = await session.execute(
                select(CrawlJob).where(CrawlJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                return {
                    "id": job.id,
                    "job_type": job.job_type,
                    "url": job.url,
                    "priority": job.priority,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "sla_deadline": job.sla_deadline.isoformat() if job.sla_deadline else None,
                    "result": job.result,
                    "error": job.error
                }
            return None
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: str,
        **kwargs
    ) -> bool:
        """Update job status and other fields."""
        async with self.get_session() as session:
            result = await session.execute(
                select(CrawlJob).where(CrawlJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                job.status = status  # type: ignore[assignment]
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                
                await session.commit()
                return True
            return False
    
    async def save_document_metadata(self, doc_data: Dict[str, Any]) -> bool:
        """Save or update document metadata."""
        async with self.get_session() as session:
            # Check if document exists
            result = await session.execute(
                select(Document).where(Document.url == doc_data.get("url"))
            )
            doc = result.scalar_one_or_none()
            
            if doc:
                # Update existing
                for key, value in doc_data.items():
                    if hasattr(doc, key):
                        setattr(doc, key, value)
            else:
                # Create new
                doc = Document(**doc_data)
                session.add(doc)
            
            await session.commit()
            return True


# Global PostgreSQL client instance
postgres_client = PostgresClient()