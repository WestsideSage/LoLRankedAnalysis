"""
Configuration management for LoL Analysis
"""
import os
from dotenv import load_dotenv


class Config:
    """Configuration manager for the application"""

    def __init__(self):
        load_dotenv()

        self.riot_api_key = os.getenv('RIOT_API_KEY', '')
        self.default_summoner_name = os.getenv('SUMMONER_NAME', '')
        self.default_tag_line = os.getenv('TAG_LINE', 'NA1')
        self.default_region = os.getenv('REGION', 'na1')

    def is_configured(self) -> bool:
        return bool(self.riot_api_key)
