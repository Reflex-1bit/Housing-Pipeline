"""
Database Manager - MySQL Connection and Query Handler
=====================================================
Handles all database operations including connection pooling,
query execution, and data persistence for housing listings.
"""

import aiomysql
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MySQL database connections and operations."""
    
    def __init__(self, database_url: str):
        """
        Initialize database manager.
        
        Args:
            database_url: MySQL connection string
        """
        self.database_url = database_url
        self.pool = None
        
    async def initialize(self):
        """Create connection pool and initialize database schema."""
        try:
            # Parse connection URL
            # Format: mysql://user:password@host:port/database
            parts = self.database_url.replace('mysql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            host_port = host_db[0].split(':')
            
            # Create connection pool
            self.pool = await aiomysql.create_pool(
                host=host_port[0],
                port=int(host_port[1]) if len(host_port) > 1 else 3306,
                user=user_pass[0],
                password=user_pass[1],
                db=host_db[1],
                autocommit=True,
                minsize=1,
                maxsize=10
            )
            
            logger.info("Database connection pool created")
            
            # Initialize schema
            await self._create_tables()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        create_listings_table = """
        CREATE TABLE IF NOT EXISTS listings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            location VARCHAR(255) NOT NULL,
            bedrooms INT,
            bathrooms INT,
            amenities JSON,
            contact VARCHAR(255),
            url VARCHAR(512),
            source VARCHAR(100),
            date_posted DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_scraped DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            INDEX idx_location (location),
            INDEX idx_price (price),
            INDEX idx_date_posted (date_posted)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(create_listings_table)
                logger.info("Database tables verified/created")
    
    async def insert_listings(self, listings: List[Dict]) -> int:
        """
        Insert new housing listings into database.
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            Number of listings inserted
        """
        if not listings:
            return 0
        
        insert_query = """
        INSERT INTO listings 
        (title, description, price, location, bedrooms, bathrooms, 
         amenities, contact, url, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        inserted = 0
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for listing in listings:
                    try:
                        # Check if listing already exists
                        if await self._listing_exists(cursor, listing.get('url')):
                            continue
                        
                        await cursor.execute(insert_query, (
                            listing.get('title'),
                            listing.get('description'),
                            listing.get('price'),
                            listing.get('location'),
                            listing.get('bedrooms'),
                            listing.get('bathrooms'),
                            listing.get('amenities'),
                            listing.get('contact'),
                            listing.get('url'),
                            listing.get('source')
                        ))
                        inserted += 1
                        
                    except Exception as e:
                        logger.error(f"Error inserting listing: {e}")
                        continue
        
        logger.info(f"Inserted {inserted} new listings")
        return inserted
    
    async def _listing_exists(self, cursor, url: str) -> bool:
        """Check if a listing with given URL already exists."""
        if not url:
            return False
        
        query = "SELECT id FROM listings WHERE url = %s LIMIT 1"
        await cursor.execute(query, (url,))
        result = await cursor.fetchone()
        return result is not None
    
    async def search_listings(self, filters: Dict) -> List[Dict]:
        """
        Search for housing listings based on filters.
        
        Args:
            filters: Dictionary containing search criteria
                - location: str
                - max_price: int
                - min_bedrooms: int
                
        Returns:
            List of matching listings
        """
        query = "SELECT * FROM listings WHERE is_active = TRUE"
        params = []
        
        if filters.get('location'):
            query += " AND location LIKE %s"
            params.append(f"%{filters['location']}%")
        
        if filters.get('max_price'):
            query += " AND price <= %s"
            params.append(filters['max_price'])
        
        if filters.get('min_bedrooms'):
            query += " AND bedrooms >= %s"
            params.append(filters['min_bedrooms'])
        
        query += " ORDER BY date_posted DESC LIMIT 50"
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                results = await cursor.fetchall()
                return results
    
    async def get_listing_by_id(self, listing_id: int) -> Optional[Dict]:
        """
        Retrieve a specific listing by ID.
        
        Args:
            listing_id: Database ID of the listing
            
        Returns:
            Listing dictionary or None if not found
        """
        query = "SELECT * FROM listings WHERE id = %s"
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (listing_id,))
                result = await cursor.fetchone()
                return result
    
    async def get_recent_listings(self, count: int = 10) -> List[Dict]:
        """
        Get most recent housing listings.
        
        Args:
            count: Number of listings to retrieve
            
        Returns:
            List of recent listings
        """
        query = """
        SELECT * FROM listings 
        WHERE is_active = TRUE 
        ORDER BY date_posted DESC 
        LIMIT %s
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (count,))
                results = await cursor.fetchall()
                return results
    
    async def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        stats_query = """
        SELECT 
            COUNT(*) as total,
            AVG(price) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM listings 
        WHERE is_active = TRUE
        """
        
        week_ago = datetime.now() - timedelta(days=7)
        new_query = """
        SELECT COUNT(*) as new_this_week 
        FROM listings 
        WHERE date_posted >= %s
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Get main stats
                await cursor.execute(stats_query)
                stats = await cursor.fetchone()
                
                # Get new listings count
                await cursor.execute(new_query, (week_ago,))
                new_count = await cursor.fetchone()
                
                stats['new_this_week'] = new_count['new_this_week']
                return stats
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed")
