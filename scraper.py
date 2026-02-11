"""
Housing Scraper - Web Scraping Module
=====================================
Scrapes housing listings from various community sources
and normalizes data for database storage.
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class HousingScraper:
    """Scrapes housing listings from multiple sources."""
    
    def __init__(self):
        """Initialize scraper with source configurations."""
        self.sources = [
            {
                'name': 'reddit_waterloo',
                'url': 'https://www.reddit.com/r/uwaterloo/search/?q=housing&sort=new',
                'parser': self._parse_reddit
            },
            {
                'name': 'facebook_marketplace',
                'url': 'https://www.facebook.com/marketplace/category/property',
                'parser': self._parse_facebook
            }
            # Add more sources as needed
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_all_sources(self) -> List[Dict]:
        """
        Scrape all configured sources concurrently.
        
        Returns:
            List of normalized listing dictionaries
        """
        tasks = [self._scrape_source(source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_listings = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scraping error: {result}")
                continue
            all_listings.extend(result)
        
        logger.info(f"Scraped {len(all_listings)} total listings")
        return all_listings
    
    async def _scrape_source(self, source: Dict) -> List[Dict]:
        """
        Scrape a single source.
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            List of listings from this source
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    source['url'],
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Source {source['name']} returned {response.status}")
                        return []
                    
                    html = await response.text()
                    listings = source['parser'](html, source['name'])
                    
                    logger.info(f"Scraped {len(listings)} listings from {source['name']}")
                    return listings
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout scraping {source['name']}")
            return []
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
            return []
    
    def _parse_reddit(self, html: str, source: str) -> List[Dict]:
        """
        Parse Reddit housing posts.
        
        Args:
            html: Raw HTML content
            source: Source name
            
        Returns:
            List of parsed listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # This is a simplified example - actual Reddit scraping
        # would need to handle their dynamic content properly
        posts = soup.find_all('div', class_='Post')
        
        for post in posts[:20]:  # Limit to recent 20 posts
            try:
                title = post.find('h3').text.strip()
                
                # Extract price from title
                price = self._extract_price(title)
                if not price:
                    continue
                
                # Extract location
                location = self._extract_location(title)
                
                listing = {
                    'title': title,
                    'description': self._get_post_text(post),
                    'price': price,
                    'location': location or 'Waterloo',
                    'bedrooms': self._extract_bedrooms(title),
                    'bathrooms': None,
                    'amenities': self._extract_amenities(title),
                    'contact': None,
                    'url': self._get_post_url(post),
                    'source': source
                }
                
                listings.append(listing)
                
            except Exception as e:
                logger.debug(f"Error parsing post: {e}")
                continue
        
        return listings
    
    def _parse_facebook(self, html: str, source: str) -> List[Dict]:
        """
        Parse Facebook Marketplace listings.
        
        Args:
            html: Raw HTML content
            source: Source name
            
        Returns:
            List of parsed listings
        """
        # Facebook requires authentication and uses dynamic loading
        # This is a placeholder for demonstration
        # In production, you'd use Facebook Graph API or Selenium
        return []
    
    def _extract_price(self, text: str) -> float:
        """
        Extract price from text.
        
        Args:
            text: Text containing price information
            
        Returns:
            Price as float or None
        """
        # Match patterns like $1200, 1200/month, $1,200
        patterns = [
            r'\$\s*(\d{1,}(?:,\d{3})*)',
            r'(\d{3,4})\s*/?(?:month|mo)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    # Validate reasonable rent range
                    if 200 <= price <= 5000:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def _extract_location(self, text: str) -> str:
        """
        Extract location from text.
        
        Args:
            text: Text containing location information
            
        Returns:
            Location string or None
        """
        # Common Waterloo area locations
        locations = [
            'Waterloo', 'Kitchener', 'Cambridge',
            'Uptown', 'Downtown', 'UW Campus',
            'Laurier', 'Conestoga', 'University District'
        ]
        
        text_lower = text.lower()
        for location in locations:
            if location.lower() in text_lower:
                return location
        
        return None
    
    def _extract_bedrooms(self, text: str) -> int:
        """
        Extract number of bedrooms from text.
        
        Args:
            text: Text containing bedroom information
            
        Returns:
            Number of bedrooms or None
        """
        # Match patterns like "2 bed", "2br", "2 bedroom"
        pattern = r'(\d+)\s*(?:bed|br|bedroom)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                bedrooms = int(match.group(1))
                if 1 <= bedrooms <= 10:
                    return bedrooms
            except ValueError:
                pass
        
        return None
    
    def _extract_amenities(self, text: str) -> List[str]:
        """
        Extract amenities from text.
        
        Args:
            text: Text containing amenity information
            
        Returns:
            List of amenities
        """
        amenity_keywords = [
            'laundry', 'parking', 'utilities', 'furnished',
            'wifi', 'gym', 'pool', 'ac', 'heating',
            'dishwasher', 'balcony', 'pets'
        ]
        
        text_lower = text.lower()
        found_amenities = []
        
        for amenity in amenity_keywords:
            if amenity in text_lower:
                found_amenities.append(amenity.capitalize())
        
        return found_amenities
    
    def _get_post_text(self, post_element) -> str:
        """Extract post description text."""
        try:
            content = post_element.find('div', class_='content')
            if content:
                return content.text.strip()[:500]  # Limit length
        except:
            pass
        return ""
    
    def _get_post_url(self, post_element) -> str:
        """Extract post URL."""
        try:
            link = post_element.find('a', href=True)
            if link:
                href = link['href']
                if not href.startswith('http'):
                    href = 'https://reddit.com' + href
                return href
        except:
            pass
        return ""


# Example manual listing addition (for testing or manual entries)
class ManualListingManager:
    """Handles manually added listings."""
    
    @staticmethod
    def create_listing(
        title: str,
        price: float,
        location: str,
        **kwargs
    ) -> Dict:
        """
        Create a manually entered listing.
        
        Args:
            title: Listing title
            price: Monthly rent
            location: Location/area
            **kwargs: Additional fields
            
        Returns:
            Normalized listing dictionary
        """
        return {
            'title': title,
            'description': kwargs.get('description', ''),
            'price': price,
            'location': location,
            'bedrooms': kwargs.get('bedrooms'),
            'bathrooms': kwargs.get('bathrooms'),
            'amenities': kwargs.get('amenities', []),
            'contact': kwargs.get('contact'),
            'url': kwargs.get('url'),
            'source': 'manual'
        }
