"""Pipeline configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class PipelineSettings(BaseSettings):
    """Pipeline configuration loaded from environment variables or .env file."""

    # Redpanda / Kafka
    redpanda_brokers: str = "localhost:9092"

    # Redis (for publishing stats)
    redis_url: str = "redis://:12345678@localhost:6379/0"

    # Zeek log directory
    zeek_log_dir: str = "/zeek-logs"

    # Normalizer
    batch_size: int = 1000
    watch_poll_interval: float = 2.0  # seconds

    # Sensor source identifier
    sensor_source: str = "zeek"

    model_config = {
        "env_file": ".env",
        "env_prefix": "PIPELINE_",
        "case_sensitive": False,
    }


settings = PipelineSettings()
