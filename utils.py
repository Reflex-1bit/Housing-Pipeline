"""
Utilities - Helper Functions
============================
Common utility functions used across the application.
"""

from typing import Dict, List
import re


def format_listing(listing: Dict) -> str:
    """
    Format a listing dictionary for display.
    
    Args:
        listing: Listing dictionary from database
        
    Returns:
        Formatted string for Discord embed
    """
    parts = []
    
    # Add bedrooms/bathrooms if available
    if listing.get('bedrooms'):
        parts.append(f"🛏️ {listing['bedrooms']} bed")
    if listing.get('bathrooms'):
        parts.append(f"🚿 {listing['bathrooms']} bath")
    
    # Add ID for reference
    parts.append(f"ID: {listing['id']}")
    
    # Add description preview
    if listing.get('description'):
        desc = listing['description'][:100]
        if len(listing['description']) > 100:
            desc += "..."
        parts.append(f"\n{desc}")
    
    return " • ".join(parts) if parts else "No additional details"


def validate_price_range(price: int) -> bool:
    """
    Validate that price is within reasonable range.
    
    Args:
        price: Price to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 < price <= 10000


def validate_bedrooms(bedrooms: int) -> bool:
    """
    Validate bedroom count.
    
    Args:
        bedrooms: Number of bedrooms
        
    Returns:
        True if valid, False otherwise
    """
    return 1 <= bedrooms <= 10


def parse_search_query(query: str) -> Dict:
    """
    Parse natural language search query into filter dictionary.
    
    Args:
        query: User's search query (e.g., "2 bedroom waterloo under 1000")
        
    Returns:
        Dictionary of parsed filters
    """
    filters = {}
    query_lower = query.lower()
    
    # Extract price
    price_patterns = [
        r'under\s+\$?(\d+)',
        r'below\s+\$?(\d+)',
        r'max\s+\$?(\d+)',
        r'\$?(\d+)\s+max'
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                filters['max_price'] = int(match.group(1))
                break
            except ValueError:
                pass
    
    # Extract bedrooms
    bed_pattern = r'(\d+)\s*(?:bed|bedroom)'
    match = re.search(bed_pattern, query_lower)
    if match:
        try:
            filters['min_bedrooms'] = int(match.group(1))
        except ValueError:
            pass
    
    # Extract location
    locations = ['waterloo', 'kitchener', 'cambridge', 'uptown', 'downtown']
    for location in locations:
        if location in query_lower:
            filters['location'] = location.capitalize()
            break
    
    return filters


def format_price(price: float) -> str:
    """
    Format price with proper currency formatting.
    
    Args:
        price: Price value
        
    Returns:
        Formatted price string
    """
    return f"${price:,.2f}"


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent SQL injection and XSS.
    
    Args:
        text: User input text
        
    Returns:
        Sanitized text
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>\"\'%;()&+]', '', text)
    return sanitized.strip()


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunked lists
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def extract_contact_info(text: str) -> Dict:
    """
    Extract contact information from text.
    
    Args:
        text: Text containing potential contact info
        
    Returns:
        Dictionary with extracted contact details
    """
    contact = {}
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact['email'] = email_match.group(0)
    
    # Extract phone
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact['phone'] = phone_match.group(0)
    
    return contact


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return url_pattern.match(url) is not None
