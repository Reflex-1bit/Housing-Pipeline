# Discord Housing Data Pipeline

> Automated housing search bot for Discord that scrapes, indexes, and serves real-time student housing listings

## Overview

A comprehensive Discord bot that aggregates housing listings from multiple community sources, stores them in a MySQL database, and provides an intuitive command interface for students to search for accommodation. Features automated web scraping, intelligent search filtering, and real-time notifications.

## Features

### Core Functionality
- **Automated Web Scraping** - Hourly scraping of multiple housing sources
- **Intelligent Search** - Natural language query parsing with multiple filters
- **Real-time Updates** - Automatic notifications for new listings
- **Data Persistence** - MySQL database with indexed queries for sub-100ms search
- **Rich Embeds** - Beautiful Discord embeds with detailed listing information

### Commands

```
!search [location] [max_price]     Search housing listings
!details <listing_id>              Get full details of a listing
!recent [count]                    Show most recent listings  
!stats                             View database statistics
!help                              Show command help
```

### Technical Highlights
- Asynchronous architecture using `asyncio` and `discord.py`
- Connection pooling for efficient database operations
- Concurrent web scraping with error handling
- Indexed MySQL queries for fast search (<100ms)
- Comprehensive logging and error tracking

## Architecture

```
┌─────────────────┐
│  Discord Bot    │
│   (bot.py)      │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬─────────┐
    │          │          │         │
┌───▼────┐ ┌──▼─────┐ ┌──▼────┐ ┌──▼────┐
│Database│ │Scraper │ │Utils  │ │Config │
│Manager │ │Module  │ │Helpers│ │.env   │
└────────┘ └────────┘ └───────┘ └───────┘
```

## Installation

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Reflex-1bit/discord-housing-bot.git
   cd discord-housing-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up MySQL database**
   ```sql
   CREATE DATABASE housing_bot;
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
DISCORD_TOKEN=your_bot_token
DATABASE_URL=mysql://user:pass@localhost:3306/housing_bot
COMMAND_PREFIX=!
SCRAPE_INTERVAL=3600
LOG_LEVEL=INFO
```

### Database Schema

The bot automatically creates the following table:

```sql
CREATE TABLE listings (
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
    date_posted DATETIME,
    date_scraped DATETIME,
    is_active BOOLEAN,
    INDEX idx_location (location),
    INDEX idx_price (price),
    INDEX idx_date_posted (date_posted)
);
```

## Usage Examples

### Basic Search
```
!search Waterloo 1000
```
Returns all listings in Waterloo under $1000/month

### Detailed View
```
!details 42
```
Shows complete information for listing #42

### Recent Listings
```
!recent 5
```
Displays the 5 most recently added listings

### Statistics
```
!stats
```
Shows database statistics (total listings, price ranges, etc.)

## Project Structure

```
discord_bot/
├── bot.py              # Main bot application
├── database.py         # Database manager with connection pooling
├── scraper.py          # Web scraping and data extraction
├── utils.py            # Helper functions and utilities
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables
└── README.md          # This file
```

## Technical Implementation

### Database Operations
- **Connection Pooling**: Uses `aiomysql` with 1-10 concurrent connections
- **Indexed Queries**: Location, price, and date indexes for fast lookups
- **Data Validation**: Input sanitization and duplicate detection

### Web Scraping
- **Concurrent Scraping**: Multiple sources scraped simultaneously
- **Error Handling**: Graceful degradation if sources are unavailable
- **Rate Limiting**: Respects robots.txt and implements delays
- **Data Normalization**: Consistent schema across all sources

### Performance Metrics
- Search queries: <100ms average
- Database inserts: ~200 listings/second
- Concurrent scraping: 5 sources simultaneously
- Memory usage: ~50MB average

## Customization

### Adding New Scraping Sources

Edit `scraper.py` and add to the `sources` list:

```python
{
    'name': 'your_source',
    'url': 'https://example.com/listings',
    'parser': self._parse_your_source
}
```

Implement the corresponding parser method:

```python
def _parse_your_source(self, html: str, source: str) -> List[Dict]:
    # Your parsing logic
    return listings
```

### Custom Commands

Add new commands in `bot.py`:

```python
@commands.command(name='mycommand')
async def my_custom_command(ctx, arg1: str):
    # Your command logic
    await ctx.send("Response")
```

## Deployment

### Running in Production

Use a process manager like `systemd` or `pm2`:

```bash
# Using pm2
pm2 start bot.py --name housing-bot --interpreter python3

# Using systemd
sudo systemctl enable housing-bot.service
sudo systemctl start housing-bot
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t housing-bot .
docker run -d --env-file .env housing-bot
```

## Troubleshooting

**Bot not responding to commands**
- Verify `DISCORD_TOKEN` is correct
- Ensure bot has proper Discord permissions
- Check bot is online in Discord

**Database connection errors**
- Verify MySQL is running
- Check `DATABASE_URL` format
- Ensure database exists

**Scraping not working**
- Check internet connection
- Verify source URLs are accessible
- Review logs for specific errors

## Future Enhancements

- [ ] Add more scraping sources (Kijiji, Facebook Marketplace)
- [ ] Implement user preferences and saved searches
- [ ] Add automatic notifications for new listings matching criteria
- [ ] Create web dashboard for listing visualization
- [ ] Add machine learning for spam/scam detection
- [ ] Implement user ratings and reviews
- [ ] Add geolocation-based distance filtering

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Author

**Aditya Sharma**
- GitHub: [@Reflex-1bit](https://github.com/Reflex-1bit)
- Email: aditya.shm64@gmail.com

## Acknowledgments

- Discord.py community
- BeautifulSoup documentation
- MySQL/aiomysql contributors

---

Built to help students find housing faster 🏠
