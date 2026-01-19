"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Neo4j Configuration
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str
    
    # PostgreSQL Configuration
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "africgraph"
    postgres_user: str = "africgraph"
    postgres_password: str
    
    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    
    # RabbitMQ Configuration
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "africgraph"
    rabbitmq_password: str
    rabbitmq_vhost: str = "/"
    
    # Elasticsearch Configuration
    elasticsearch_host: str = "elasticsearch"
    elasticsearch_port: int = 9200
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Email Configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    
    # OAuth Configuration
    xero_client_id: str = ""
    xero_client_secret: str = ""
    quickbooks_client_id: str = ""
    quickbooks_client_secret: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
