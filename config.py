"""
Configuration - Environment Variables and Settings
=================================================
Centralized configuration management for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Discord Bot Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'mysql://user:password@localhost:3306/housing_bot'
    )
    
    # Scraper Configuration
    SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', '3600'))  # seconds
    MAX_CONCURRENT_SCRAPES = int(os.getenv('MAX_CONCURRENT_SCRAPES', '5'))
    
    # Application Settings
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', '50'))
    LISTING_CACHE_TTL = int(os.getenv('LISTING_CACHE_TTL', '300'))  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
    
    @classmethod
    def display(cls):
        """Display current configuration (hide sensitive data)."""
        print("=" * 50)
        print("Configuration:")
        print(f"  Command Prefix: {cls.COMMAND_PREFIX}")
        print(f"  Database: {cls.DATABASE_URL.split('@')[1] if '@' in cls.DATABASE_URL else 'Not set'}")
        print(f"  Scrape Interval: {cls.SCRAPE_INTERVAL}s")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print("=" * 50)
