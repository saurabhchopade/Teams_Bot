"""Configuration settings for the Teams Interview Bot."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure AD Configuration
    azure_client_id: str = Field(..., env="AZURE_CLIENT_ID")
    azure_client_secret: str = Field(..., env="AZURE_CLIENT_SECRET")
    azure_tenant_id: str = Field(..., env="AZURE_TENANT_ID")
    
    # Bot Framework Configuration
    bot_app_id: str = Field(..., env="BOT_APP_ID")
    bot_app_password: str = Field(..., env="BOT_APP_PASSWORD")
    bot_endpoint: str = Field(..., env="BOT_ENDPOINT")
    
    # Azure Speech Services
    azure_speech_key: str = Field(..., env="AZURE_SPEECH_KEY")
    azure_speech_region: str = Field("eastus", env="AZURE_SPEECH_REGION")
    
    # Google Gemini Configuration
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    gemini_model: str = Field("gemini-2.0-flash-exp", env="GEMINI_MODEL")
    
    # Application Settings
    callback_url: str = Field(..., env="CALLBACK_URL")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    interview_duration_minutes: int = Field(45, env="INTERVIEW_DURATION_MINUTES")
    max_questions: int = Field(15, env="MAX_QUESTIONS")
    
    # Optional Database
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    
    # Microsoft Graph API Endpoints
    graph_base_url: str = "https://graph.microsoft.com/v1.0"
    graph_beta_url: str = "https://graph.microsoft.com/beta"
    
    # Required Microsoft Graph Permissions
    required_scopes: list = [
        "https://graph.microsoft.com/OnlineMeetings.ReadWrite.All",
        "https://graph.microsoft.com/Calls.AccessMedia.All",
        "https://graph.microsoft.com/Calls.JoinGroupCall.All",
        "https://graph.microsoft.com/CallRecords.Read.All"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()