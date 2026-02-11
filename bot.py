"""
Discord Housing Bot - Main Entry Point
======================================
A Discord bot that provides real-time housing search functionality
for students by scraping and indexing housing listings from community sources.

Author: Aditya Sharma
Repository: github.com/Reflex-1bit
"""

import discord
from discord.ext import commands
import asyncio
import logging
from config import Config
from database import DatabaseManager
from scraper import HousingScraper
from utils import format_listing, validate_price_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HousingBot(commands.Bot):
    """Main bot class handling Discord interactions and housing search."""
    
    def __init__(self):
        """Initialize the bot with required intents and configuration."""
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=commands.DefaultHelpCommand()
        )
        
        self.db = DatabaseManager(Config.DATABASE_URL)
        self.scraper = HousingScraper()
        
    async def setup_hook(self):
        """Initialize database and start background tasks."""
        logger.info("Initializing database...")
        await self.db.initialize()
        
        logger.info("Starting background scraper...")
        self.bg_scraper.start()
        
        logger.info("Bot setup complete")
    
    async def on_ready(self):
        """Event handler for when bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Connected to {len(self.guilds)} guild(s)')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="housing listings | !help"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """Global error handler for commands."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Use `!help` to see available commands.")
        else:
            logger.error(f"Unexpected error: {error}", exc_info=True)
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
    
    @commands.Cog.listener()
    async def bg_scraper(self):
        """Background task to scrape housing listings periodically."""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                logger.info("Starting scraping cycle...")
                new_listings = await self.scraper.scrape_all_sources()
                
                if new_listings:
                    await self.db.insert_listings(new_listings)
                    logger.info(f"Added {len(new_listings)} new listings")
                
                # Wait 1 hour before next scrape
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in background scraper: {e}", exc_info=True)
                await asyncio.sleep(600)  # Wait 10 min on error


# ====================
# COMMAND DEFINITIONS
# ====================

@commands.command(name='search')
async def search_housing(ctx, location: str = None, max_price: int = None):
    """
    Search for housing listings.
    
    Usage:
        !search <location> <max_price>
        !search Waterloo 1000
        !search "University District" 1500
    
    Parameters:
        location: City/area to search in (optional)
        max_price: Maximum monthly rent (optional)
    """
    try:
        # Build search criteria
        filters = {}
        if location:
            filters['location'] = location
        if max_price:
            if not validate_price_range(max_price):
                await ctx.send("❌ Invalid price. Must be between 0 and 10000.")
                return
            filters['max_price'] = max_price
        
        # Query database
        listings = await ctx.bot.db.search_listings(filters)
        
        if not listings:
            await ctx.send("🔍 No listings found matching your criteria.")
            return
        
        # Create embed for results
        embed = discord.Embed(
            title="🏠 Housing Search Results",
            description=f"Found {len(listings)} listing(s)",
            color=discord.Color.blue()
        )
        
        # Add top 5 results
        for listing in listings[:5]:
            embed.add_field(
                name=f"${listing['price']}/month - {listing['location']}",
                value=format_listing(listing),
                inline=False
            )
        
        if len(listings) > 5:
            embed.set_footer(text=f"Showing 5 of {len(listings)} results. Refine your search for more specific results.")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in search command: {e}", exc_info=True)
        await ctx.send("❌ An error occurred while searching. Please try again.")


@commands.command(name='details')
async def listing_details(ctx, listing_id: int):
    """
    Get detailed information about a specific listing.
    
    Usage:
        !details <listing_id>
        !details 42
    """
    try:
        listing = await ctx.bot.db.get_listing_by_id(listing_id)
        
        if not listing:
            await ctx.send(f"❌ No listing found with ID {listing_id}")
            return
        
        embed = discord.Embed(
            title=f"🏠 Listing #{listing_id}",
            description=listing.get('description', 'No description available'),
            color=discord.Color.green()
        )
        
        embed.add_field(name="💰 Price", value=f"${listing['price']}/month", inline=True)
        embed.add_field(name="📍 Location", value=listing['location'], inline=True)
        embed.add_field(name="🛏️ Bedrooms", value=listing.get('bedrooms', 'N/A'), inline=True)
        embed.add_field(name="🚿 Bathrooms", value=listing.get('bathrooms', 'N/A'), inline=True)
        
        if listing.get('amenities'):
            embed.add_field(
                name="✨ Amenities",
                value=", ".join(listing['amenities']),
                inline=False
            )
        
        if listing.get('contact'):
            embed.add_field(name="📧 Contact", value=listing['contact'], inline=False)
        
        if listing.get('url'):
            embed.add_field(name="🔗 Link", value=listing['url'], inline=False)
        
        embed.set_footer(text=f"Listed on {listing.get('date_posted', 'Unknown')}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in details command: {e}", exc_info=True)
        await ctx.send("❌ An error occurred. Please try again.")


@commands.command(name='recent')
async def recent_listings(ctx, count: int = 10):
    """
    Show most recent housing listings.
    
    Usage:
        !recent [count]
        !recent 5
    """
    try:
        if count < 1 or count > 20:
            await ctx.send("❌ Count must be between 1 and 20")
            return
        
        listings = await ctx.bot.db.get_recent_listings(count)
        
        if not listings:
            await ctx.send("🔍 No recent listings found.")
            return
        
        embed = discord.Embed(
            title="🆕 Recent Housing Listings",
            description=f"Latest {len(listings)} listing(s)",
            color=discord.Color.purple()
        )
        
        for listing in listings:
            embed.add_field(
                name=f"ID {listing['id']} - ${listing['price']}/mo",
                value=f"📍 {listing['location']}\n{listing.get('description', '')[:100]}...",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in recent command: {e}", exc_info=True)
        await ctx.send("❌ An error occurred. Please try again.")


@commands.command(name='stats')
async def housing_stats(ctx):
    """Display statistics about available housing listings."""
    try:
        stats = await ctx.bot.db.get_statistics()
        
        embed = discord.Embed(
            title="📊 Housing Database Statistics",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Total Listings", value=stats['total'], inline=True)
        embed.add_field(name="Avg Price", value=f"${stats['avg_price']:.2f}", inline=True)
        embed.add_field(name="Min Price", value=f"${stats['min_price']}", inline=True)
        embed.add_field(name="Max Price", value=f"${stats['max_price']}", inline=True)
        embed.add_field(name="New This Week", value=stats['new_this_week'], inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}", exc_info=True)
        await ctx.send("❌ An error occurred. Please try again.")


# Register commands to bot
def setup_commands(bot):
    """Register all commands with the bot."""
    bot.add_command(search_housing)
    bot.add_command(listing_details)
    bot.add_command(recent_listings)
    bot.add_command(housing_stats)


def main():
    """Main entry point for the bot."""
    bot = HousingBot()
    setup_commands(bot)
    
    try:
        bot.run(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
