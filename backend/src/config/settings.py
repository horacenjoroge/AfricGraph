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
    jwt_refresh_expiration_days: int = 7
    
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
    
    # Xero
    xero_client_id: str = ""
    xero_client_secret: str = ""
    xero_redirect_uri: str = "http://localhost:8000/callback/xero"
    # QuickBooks
    quickbooks_client_id: str = ""
    quickbooks_client_secret: str = ""
    quickbooks_redirect_uri: str = "http://localhost:8000/callback/quickbooks"
    quickbooks_environment: str = "sandbox"  # sandbox | production
    # Odoo
    odoo_url: str = ""
    odoo_db: str = ""
    odoo_username: str = ""
    odoo_password: str = ""
    # Accounting connector defaults
    accounting_request_timeout: int = 30
    accounting_retry_max: int = 3
    accounting_rate_limit_delay: float = 1.0
    # Normalization
    normalization_target_currency: str = "USD"
    authoritative_sources_order: List[str] = []  # e.g. ["xero", "quickbooks", "odoo"] for merge
    # Ingestion / Celery
    celery_broker_url: str = ""  # default from rabbitmq if empty
    default_business_id: str = "default"  # for Business-ISSUED-Invoice when no business in source
    ingestion_mobile_money_path: str = ""  # for scheduled run; empty = disabled
    ingestion_mobile_money_provider: str = "mpesa"
    ingestion_accounting_connector: str = ""  # xero|quickbooks|odoo; empty = disabled
    ingestion_accounting_tenant_id: str = ""
    # Deduplication
    deduplication_auto_merge_confidence_threshold: float = 0.95
    deduplication_candidates_limit: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
