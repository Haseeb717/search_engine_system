"""
Configuration management using Pydantic Settings.
Loads from environment variables.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "SearchEngine"
    app_env: str = "development"
    debug: bool = True
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_cache_ttl: int = 1800  # 30 minutes
    
    # Elasticsearch
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_index: str = "web_pages"
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "search_engine"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    
    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_crawl_queue: str = "crawl_queue"
    rabbitmq_recrawl_queue: str = "recrawl_queue"
    
    # S3/Storage
    s3_bucket_name: str = "search-engine-content"
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    
    # Worker Settings
    crawler_workers: int = 10
    max_concurrent_requests: int = 100
    crawl_timeout: int = 30
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def elasticsearch_url(self) -> str:
        """Build Elasticsearch connection URL."""
        if self.elasticsearch_username and self.elasticsearch_password:
            return f"http://{self.elasticsearch_username}:{self.elasticsearch_password}@{self.elasticsearch_host}:{self.elasticsearch_port}"
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"
    
    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def rabbitmq_url(self) -> str:
        """Build RabbitMQ connection URL."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()