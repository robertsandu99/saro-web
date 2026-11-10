# settings.py - Application settings loaded from environment variables and .env file

import functools

from pydantic import Field # lets you describe a variable with extra information
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    Uses pydantic-settings for type validation and defaults.

    # Fields: lets you describe a variable with extra information. Field with no 'default=' argument means required.
    # BaseSettings: a special pydantic class that knows how to read values from environment variables and .env files
    # SettingsConfigDict: configuration for how pydantic-settings should load the settings,  configuring how BaseSettings reads those values
    """
    # ── Database (required — no default, app refuses to start without it) ──
    db_conn: str = Field(description="PostgreSQL async connection string")

    # ── Security (required — no default) ──────────────────────────────────
    secret_key: str = Field(description="JWT signing secret, min 32 chars")

    # ── Application ────────────────────────────────────────────────────────
    debug: bool = Field(default=False, description="Enable debug mode")
    app_name: str = Field(default="saro-web", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")

    model_config = SettingsConfigDict(
        env_file=".env",    # look for a file named .env in the current directory and read it
        env_prefix="SARO_", # look for environment variables that start with SARO_
        case_sensitive=False, # 'PREFIX_DEBUG' and 'prefix_debug' are treated the same
        extra="ignore", # if the .env file has variables we don't have a field for, ignore them instead of crashing
    )


@functools.lru_cache
def get_settings() -> Settings:
    """
    A function that creates and returns a Settings object (which triggers the .env file reading).
    Return cached settings instance. Call get_settings.cache_clear() in tests.
    
    lru_cache means "the first time this function is called, run it and remember the result. 
    Every time after that, return the remembered result without running it again." 
    This means .env is read exactly once at startup, not on every request
    """
    return Settings()
