from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "AI Data Copilot"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # IBM watsonx.ai
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    WATSONX_MODEL_ID: str = "ibm/granite-13b-chat-v2"
    WATSONX_MAX_NEW_TOKENS: int = 512
    WATSONX_TEMPERATURE: float = 0.0
    # Set to True to use mock LLM responses (no API key required)
    WATSONX_MOCK: bool = True

    # IBM Consulting Advantage (ICA)
    ICA_KEY: str = ""
    ICA_BASE_URL: str = "https://api.nextgen-beta.ica.ibm.com/ica/v1"
    # Chat model ID to use for NL→SQL generation via /chat-models/chat/completions
    ICA_MODEL_ID: str = "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
    # Set to False to route NL→SQL through the real ICA API
    ICA_MOCK: bool = True

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/copilot"
    # Set to True to use in-memory SQLite mock data (no real DB required)
    DB_MOCK: bool = True

    # AWS Athena
    # Set USE_ATHENA=True to run queries against real AWS Athena in production
    USE_ATHENA: bool = False
    ATHENA_DB: str = "default"
    ATHENA_OUTPUT: str = ""          # e.g. s3://my-bucket/athena-results/
    AWS_REGION: str = "us-east-1"

    # Conversation memory
    # Maximum number of past interactions kept per user in the rolling window
    MEMORY_MAX_HISTORY: int = 10

    # Audit logging
    AUDIT_ENABLED: bool = True
    # Path to the JSON-lines audit log file (relative to CWD)
    AUDIT_LOG_FILE: str = "logs/audit.log"

    # Future: Vector store
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""

    # Anomaly detection thresholds (per-request overrides take precedence)
    # Coefficient of variation (%) above which a column is flagged as highly variable
    ANOMALY_VARIATION_THRESHOLD: float = 30.0
    # IQR fence multiplier for outlier detection (standard Tukey = 1.5)
    ANOMALY_IQR_MULTIPLIER: float = 1.5

    # Security
    API_KEY_HEADER: str = "X-API-Key"
    SECRET_KEY: str = "change-me-in-production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
