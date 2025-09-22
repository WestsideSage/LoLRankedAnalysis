"""
Configuration management for LoL Analysis
"""
import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the application"""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        self.riot_api_key = self.get_env_var('RIOT_API_KEY')
        self.default_summoner_name = os.getenv('SUMMONER_NAME', '')
        self.default_region = os.getenv('REGION', 'na1')
    
    def get_env_var(self, var_name: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value
    
    def is_configured(self) -> bool:
        """Check if required configuration is available"""
        try:
            self.get_env_var('RIOT_API_KEY')
            return True
        except ValueError:
            return False