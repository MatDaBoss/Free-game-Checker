#!/usr/bin/env python3
"""
Free Game Checker V2.0 - Main Application
Monitors game stores for free games with platform support
"""

import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import schedule
import time
import logging
from pathlib import Path
import sqlite3
from typing import List, Dict
import re
from urllib.parse import urljoin
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/free-game-checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_FILE = '/etc/free-game-checker/config.json'
DB_FILE = '/var/lib/free-game-checker/games.db'

# Platform order for sorting
PLATFORM_ORDER = {'PC': 1, 'Xbox': 2, 'Nintendo Switch': 3, 'Android': 4}

class GameScraper:
    """Base class for game store scrapers"""
    
    def __init__(self, store_name: str, platform: str = 'PC'):
        self.store_name = store_name
        self.platform = platform
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape(self) -> List[Dict]:
        """Override this method in subclasses"""
        raise NotImplementedError

class EpicGamesScraper(GameScraper):
    """Epic Games Store - Weekly free games"""
    
    def __init__(self):
        super().__init__("Epic Games Store", "PC")
        self.api_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    
    def scrape(self) -> List[Dict]:
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
            
            for game in elements:
                promotions = game.get('promotions', {})
                if not promotions:
                    continue
                
                promotional_offers = promotions.get('promotionalOffers', [])
                if not promotional_offers:
                    continue
                
                for offer_set in promotional_offers:
                    for offer in offer_set.get('promotionalOffers', []):
                        discount_percentage = offer.get('discountSetting', {}).get('discountPercentage', 0)
                        if discount_percentage == 0:
                            title = game.get('title', 'Unknown Game')
                            description = game.get('description', 'No description available')
                            
                            image_url = None
                            for image in game.get('keyImages', []):
                                if image.get('type') in ['DieselStoreFrontWide', 'OfferImageWide']:
                                    image_url = image.get('url')
                                    break
                            
                            end_date = offer.get('endDate', '')
                            original_price = game.get('price', {}).get('totalPrice', {}).get('fmtPrice', {}).get('originalPrice', 'N/A')
                            slug = game.get('productSlug', '')
                            game_url = f"https://store.epicgames.com/en-US/p/{slug}" if slug else "https://store.epicgames.com/en-US/free-games"
                            
                            games.append({
                                'title': title,
                                'store': self.store_name,
                                'platform': self.platform,
                                'description': description[:200] + '...' if len(description) > 200 else description,
                                'image_url': image_url,
                                'game_url': game_url,
                                'original_price': original_price,
                                'end_date': end_date,
                                'store_logo': 'https://cdn2.unrealengine.com/epic-games-logo-400x400-400x400-8b560c1e48a1.png'
                            })
            
            logger.info(f"Found {len(games)} free games on Epic Games Store")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Epic Games Store: {e}")
            return []

class SteamScraper(GameScraper):
    """Steam - Free to Keep games (was paid, now free forever)"""
    
    def __init__(self):
        super().__init__("Steam", "PC")
    
    def scrape(self) -> List[Dict]:
        try:
            # SteamDB's Free to Keep page - games that are temporarily free
            url = "https://steamdb.info/upcoming/free/"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            games = []
            
            # Find the table with free to keep games
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows[:10]:  # Limit to 10
                    try:
                        cols = row.find_all('td')
                        if len(cols) < 3:
                            continue
                        
                        # Get game name
                        name_cell = cols[1]
                        title_link = name_cell.find('a')
                        if not title_link:
                            continue
                        
                        title = title_link.get_text().strip()
                        app_id = title_link.get('href', '').split('/')[-2] if '/' in title_link.get('href', '') else ''
                        
                        # Get end date
                        date_cell = cols[2] if len(cols) > 2 else None
                        end_date = date_cell.get_text().strip() if date_cell else ''
                        
                        # Construct Steam store URL
                        game_url = f"https://store.steampowered.com/app/{app_id}/" if app_id else "https://store.steampowered.com"
                        
                        # Try to get image from Steam API
                        image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg" if app_id else ''
                        
                        games.append({
                            'title': title,
                            'store': self.store_name,
                            'platform': self.platform,
                            'description': 'Free to Keep! Claim now and keep forever. Limited time offer.',
                            'image_url': image_url,
                            'game_url': game_url,
                            'original_price': 'Was Paid',
                            'end_date': end_date,
                            'store_logo': 'https://store.cloudflare.steamstatic.com/public/shared/images/header/logo_steam.svg'
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing Steam game: {e}")
                        continue
            
            logger.info(f"Found {len(games)} Free to Keep games on Steam")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Steam: {e}")
            return []

class GOGScraper(GameScraper):
    """GOG - Free games (rare)"""
    
    def __init__(self):
        super().__init__("GOG", "PC")
    
    def scrape(self) -> List[Dict]:
        try:
            # GOG occasionally offers free games
            url = "https://www.gog.com/en/games?priceRange=0,0&discounted=true"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            games = []
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # GOG uses dynamic content, check for product cards
            product_cards = soup.find_all('a', class_=lambda x: x and 'product-tile' in str(x))
            
            for card in product_cards[:10]:
                try:
                    title_elem = card.find(['span', 'div'], class_=lambda x: x and 'title' in str(x).lower())
                    if title_elem:
                        title = title_elem.get_text().strip()
                        game_url = urljoin('https://www.gog.com', card.get('href', ''))
                        
                        img = card.find('img')
                        image_url = img.get('src', '') if img else ''
                        
                        games.append({
                            'title': title,
                            'store': self.store_name,
                            'platform': self.platform,
                            'description': 'Free game on GOG',
                            'image_url': image_url,
                            'game_url': game_url,
                            'original_price': 'Special Offer',
                            'end_date': '',
                            'store_logo': 'https://www.gog.com/favicon.ico'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing GOG game: {e}")
                    continue
            
            logger.info(f"Found {len(games)} free games on GOG")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping GOG: {e}")
            return []

class HumbleBundleScraper(GameScraper):
    """Humble Bundle - Rare free game giveaways"""
    
    def __init__(self):
        super().__init__("Humble Bundle", "PC")
    
    def scrape(self) -> List[Dict]:
        try:
            # Humble Bundle rarely has "was paid, now free" games
            # They occasionally do giveaways on their store
            # Check main store page for any promotions
            url = "https://www.humblebundle.com/store"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            games = []
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any free promotions (this is rare)
            # Humble Bundle structure varies, so this is a basic check
            # Users should also check manually as these are rare events
            
            logger.info(f"Checked Humble Bundle for free games (rare)")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Humble Bundle: {e}")
            return []

class ItchIOScraper(GameScraper):
    """Itch.io - Games with 100% discount ONLY (was paid, now free)"""
    
    def __init__(self):
        super().__init__("Itch.io", "PC")
    
    def scrape(self) -> List[Dict]:
        try:
            # Itch.io on-sale page - look for 100% off games
            url = "https://itch.io/games/on-sale"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            games = []
            
            # Find all game cells
            game_cells = soup.find_all('div', class_='game_cell')
            
            for cell in game_cells:
                try:
                    # Look for the sale badge with -100%
                    sale_badge = cell.find('div', class_='sale_tag')
                    
                    # CRITICAL: Only proceed if it's -100% discount
                    if not sale_badge:
                        continue
                    
                    badge_text = sale_badge.get_text().strip()
                    if '-100%' not in badge_text:
                        continue  # Skip if not 100% off
                    
                    # Now we know it's 100% off, get the details
                    title_tag = cell.find('a', class_='title')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text().strip()
                    game_url = urljoin('https://itch.io', title_tag.get('href', ''))
                    
                    # Get image
                    img_tag = cell.find('img')
                    image_url = ''
                    if img_tag:
                        image_url = img_tag.get('data-lazy_src', '') or img_tag.get('src', '')
                    
                    # Get original price
                    price_container = cell.find('div', class_='price_value')
                    original_price = 'Was Paid'
                    
                    if price_container:
                        # Look for original price (before discount)
                        price_text = price_container.get_text()
                        # The original price is usually shown before the $0
                        if '$' in price_text:
                            import re
                            prices = re.findall(r'\$[\d.]+', price_text)
                            if len(prices) >= 2:
                                original_price = prices[0]  # First price is usually original
                            elif len(prices) == 1 and '$0' not in prices[0]:
                                original_price = prices[0]
                    
                    # Also check for sale price element
                    sale_price = cell.find('div', class_='sale_price')
                    if sale_price and not original_price.startswith('$'):
                        sale_text = sale_price.get_text().strip()
                        if '$' in sale_text:
                            original_price = sale_text.split('$')[1].split()[0]
                            original_price = f"${original_price}"
                    
                    games.append({
                        'title': title,
                        'store': self.store_name,
                        'platform': self.platform,
                        'description': f'100% OFF! Was {original_price}, now FREE on Itch.io',
                        'image_url': image_url,
                        'game_url': game_url,
                        'original_price': original_price,
                        'end_date': 'Limited time sale',
                        'store_logo': 'https://static.itch.io/images/itchio-textless-black.svg'
                    })
                    
                    if len(games) >= 10:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error parsing Itch.io game: {e}")
                    continue
            
            logger.info(f"Found {len(games)} games with -100% discount on Itch.io")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Itch.io: {e}")
            return []

class NintendoSwitchScraper(GameScraper):
    """Nintendo Switch - Only paid games that became free"""
    
    def __init__(self):
        super().__init__("Nintendo Switch", "Nintendo Switch")
    
    def scrape(self) -> List[Dict]:
        try:
            url = "https://searching.nintendo-europe.com/en/select"
            
            params = {
                'q': '*',
                'fq': 'type:GAME AND system_type:nintendoswitch* AND price_has_discount_b:true AND price_discount_percentage_f:100',
                'rows': 50,
                'sort': 'popularity desc',
                'wt': 'json'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            docs = data.get('response', {}).get('docs', [])
            
            for doc in docs:
                title = doc.get('title', '')
                if 'demo' in title.lower() or 'trial' in title.lower():
                    continue
                
                price_regular = doc.get('price_regular_f', 0)
                price_current = doc.get('price_lowest_f', 0)
                
                if price_regular > 0 and price_current == 0:
                    description = doc.get('excerpt', 'Previously paid game, now free on Nintendo eShop')
                    
                    image_url = doc.get('image_url', '')
                    if image_url and not image_url.startswith('http'):
                        image_url = f"https:{image_url}"
                    
                    nsuid = doc.get('nsuid_txt', [''])[0] if doc.get('nsuid_txt') else ''
                    game_url = f"https://www.nintendo.com/en-au/Games/{nsuid}" if nsuid else "https://www.nintendo.com/en-au/Nintendo-Switch.html"
                    
                    dates = doc.get('price_discount_percentage_eligibilities_s', [])
                    end_date = dates[0] if dates else ''
                    
                    games.append({
                        'title': title,
                        'store': self.store_name,
                        'platform': self.platform,
                        'description': description[:200] + '...' if len(description) > 200 else description,
                        'image_url': image_url,
                        'game_url': game_url,
                        'original_price': f"${price_regular:.2f}",
                        'end_date': end_date,
                        'store_logo': 'https://assets.nintendo.com/image/upload/ncom/en_US/merchandising/misc/nintendo-switch-logo.png'
                    })
            
            logger.info(f"Found {len(games)} paid games now free on Nintendo Switch")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Nintendo Switch: {e}")
            return []

class XboxScraper(GameScraper):
    """Xbox - Free game deals (was paid, now $0.00)"""
    
    def __init__(self):
        super().__init__("Xbox Store", "Xbox")
    
    def scrape(self) -> List[Dict]:
        try:
            games = []
            
            # Xbox Australian deals page filtered for free games
            deals_url = "https://www.xbox.com/en-AU/games/browse/DynamicChannel.GameDeals?Price=0"
            response = requests.get(deals_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for game elements - Xbox uses various structures
                # Try to find product cards or game listings
                game_elements = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in str(x).lower() or 'game' in str(x).lower()))
                
                for element in game_elements[:15]:
                    try:
                        # Find title
                        title_elem = element.find(['h3', 'h4', 'h2', 'a'])
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text().strip()
                        
                        # Skip if it's clearly free-to-play
                        if any(word in title.lower() for word in ['fortnite', 'warzone', 'apex legends', 'rocket league']):
                            continue
                        
                        # Get link
                        link = element.find('a', href=True)
                        game_url = urljoin('https://www.xbox.com', link['href']) if link else deals_url
                        
                        # Get image
                        img = element.find('img')
                        image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                        
                        # Check for price info
                        price_elem = element.find(['span', 'div'], class_=lambda x: x and 'price' in str(x).lower())
                        original_price = 'Was Paid'
                        if price_elem:
                            price_text = price_elem.get_text()
                            if '$' in price_text and '$0' not in price_text:
                                original_price = price_text.strip()
                        
                        games.append({
                            'title': title,
                            'store': self.store_name,
                            'platform': self.platform,
                            'description': 'Free game deal on Xbox Store. Was paid, now free!',
                            'image_url': image_url,
                            'game_url': game_url,
                            'original_price': original_price,
                            'end_date': 'Limited time',
                            'store_logo': 'https://www.xbox.com/favicon.ico'
                        })
                        
                        if len(games) >= 10:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error parsing Xbox game: {e}")
                        continue
            
            logger.info(f"Found {len(games)} free deals on Xbox")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Xbox: {e}")
            return []

class GooglePlayScraper(GameScraper):
    """Google Play Games - Android games now $0.00 (was paid)"""
    
    def __init__(self):
        super().__init__("Google Play Games", "Android")
    
    def scrape(self) -> List[Dict]:
        try:
            # Google Play games on sale collection
            url = "https://play.google.com/store/apps/collection/promotion_3002a18_gamesonsale?hl=en-US"
            
            # Add specific headers for Google Play
            headers = self.headers.copy()
            headers['Accept-Language'] = 'en-US,en;q=0.9'
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            games = []
            
            # Google Play has game cards with strikethrough prices and $0.00
            # Look for all clickable game elements
            game_links = soup.find_all('a', href=lambda x: x and '/store/apps/details?id=' in str(x))
            
            for link in game_links[:20]:  # Check more games
                try:
                    # Get parent container
                    container = link.find_parent(['div', 'article'])
                    if not container:
                        container = link
                    
                    # Find title - usually in an aria-label or direct text
                    title = link.get('aria-label', '').strip()
                    if not title:
                        title_elem = container.find(['h3', 'h4', 'div'], class_=lambda x: x and 'title' in str(x).lower())
                        if title_elem:
                            title = title_elem.get_text().strip()
                    
                    # Clean title (remove category info)
                    if title:
                        title = title.split('\n')[0].strip()
                    
                    if not title or len(title) < 2:
                        continue
                    
                    # Get URL
                    game_url = urljoin('https://play.google.com', link.get('href', ''))
                    
                    # Get image
                    img = container.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    
                    # Look for price elements
                    # Current price (should be $0.00)
                    current_price_elem = container.find(['span', 'div'], string=lambda x: x and '$0.00' in str(x))
                    
                    # Original price (strikethrough)
                    original_price_elem = container.find(['span', 'div'], class_=lambda x: x and ('original' in str(x).lower() or 'strike' in str(x).lower()))
                    if not original_price_elem:
                        # Try finding strikethrough text
                        original_price_elem = container.find(['s', 'del', 'strike'])
                    
                    # Also check aria-label for price info
                    price_text = link.get('aria-label', '')
                    
                    # Determine if it's free now with original price
                    is_free_now = False
                    original_price = None
                    
                    if current_price_elem or '$0.00' in price_text.lower():
                        is_free_now = True
                    
                    if original_price_elem:
                        original_price = original_price_elem.get_text().strip()
                    elif '$' in price_text and '$0.00' not in price_text:
                        # Extract original price from aria-label
                        import re
                        prices = re.findall(r'\$\d+\.\d+', price_text)
                        if len(prices) >= 2:  # First is original, second is current
                            original_price = prices[0]
                        elif len(prices) == 1 and is_free_now:
                            original_price = prices[0]
                    
                    # Only add if it's NOW free AND had a price before
                    if is_free_now and original_price and original_price != '$0.00':
                        games.append({
                            'title': title,
                            'store': self.store_name,
                            'platform': self.platform,
                            'description': f'Free Android game on Google Play! Was {original_price}, now $0.00',
                            'image_url': image_url,
                            'game_url': game_url,
                            'original_price': original_price,
                            'end_date': 'Limited time sale',
                            'store_logo': 'https://www.gstatic.com/android/market_images/web/favicon_v2.ico'
                        })
                        
                        if len(games) >= 10:
                            break
                            
                except Exception as e:
                    logger.warning(f"Error parsing Google Play game: {e}")
                    continue
            
            logger.info(f"Found {len(games)} free games on Google Play (was paid)")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping Google Play Games: {e}")
            return []

class PrimeGamingScraper(GameScraper):
    """Prime Gaming - Disabled"""
    
    def __init__(self):
        super().__init__("Prime Gaming", "PC")
    
    def scrape(self) -> List[Dict]:
        logger.info("Prime Gaming scraper is disabled")
        return []

class Database:
    """SQLite database handler with platform support"""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                store TEXT NOT NULL,
                platform TEXT DEFAULT 'PC',
                description TEXT,
                image_url TEXT,
                game_url TEXT,
                original_price TEXT,
                end_date TEXT,
                store_logo TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, store)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                active BOOLEAN DEFAULT 1,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                pattern TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_game(self, game: Dict):
        """Add or update a game in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO games (title, store, platform, description, image_url, game_url, original_price, end_date, store_logo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title, store) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    platform = excluded.platform,
                    description = excluded.description,
                    image_url = excluded.image_url,
                    game_url = excluded.game_url,
                    original_price = excluded.original_price,
                    end_date = excluded.end_date
            ''', (
                game['title'], game['store'], game.get('platform', 'PC'), game['description'],
                game['image_url'], game['game_url'], game['original_price'],
                game['end_date'], game.get('store_logo', '')
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error adding game to database: {e}")
        finally:
            conn.close()
    
    def get_recent_games(self, hours: int = 168) -> List[Dict]:
        """Get games seen in the last X hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT title, store, platform, description, image_url, game_url, original_price, end_date, store_logo
            FROM games
            WHERE last_seen >= ?
            ORDER BY last_seen DESC
        ''', (cutoff_time,))
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'title': row[0],
                'store': row[1],
                'platform': row[2],
                'description': row[3],
                'image_url': row[4],
                'game_url': row[5],
                'original_price': row[6],
                'end_date': row[7],
                'store_logo': row[8]
            })
        
        conn.close()
        return games
    
    def get_recipients(self) -> List[str]:
        """Get all active email recipients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT email FROM recipients WHERE active = 1')
        emails = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return emails

class EmailSender:
    """Email sender with fancy HTML templates and platform icons"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.platform_icons = {
            'PC': '🖥️',
            'Xbox': '🎮',
            'Nintendo Switch': '🕹️',
            'Android': '📱'
        }
    
    def create_html_email(self, games: List[Dict]) -> str:
        """Create fancy HTML email with game cards and platform icons"""
        
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .game-card {
            border-bottom: 1px solid #e0e0e0;
            padding: 20px;
            transition: background-color 0.3s;
        }
        .game-card:hover {
            background-color: #f9f9f9;
        }
        .game-card:last-child {
            border-bottom: none;
        }
        .game-image {
            width: 100%;
            height: auto;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .store-badge {
            display: inline-block;
            background-color: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .platform-info {
            color: #666;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .game-title {
            font-size: 22px;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }
        .price-info {
            color: #e74c3c;
            font-weight: bold;
            font-size: 18px;
            margin: 10px 0;
        }
        .price-original {
            text-decoration: line-through;
            color: #999;
            margin-right: 10px;
        }
        .price-free {
            color: #27ae60;
        }
        .game-description {
            color: #666;
            line-height: 1.6;
            margin: 10px 0;
        }
        .expiry {
            color: #e67e22;
            font-size: 14px;
            margin: 10px 0;
        }
        .claim-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            margin-top: 15px;
            transition: transform 0.2s;
        }
        .claim-button:hover {
            transform: translateY(-2px);
        }
        .footer {
            background-color: #f4f4f4;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        .divider {
            height: 2px;
            background: linear-gradient(to right, transparent, #667eea, transparent);
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Free Games Available!</h1>
            <p>Your weekly roundup of free games</p>
        </div>
"""
        
        # Add game cards
        for i, game in enumerate(games):
            platform_icon = self.platform_icons.get(game.get('platform', 'PC'), '🖥️')
            platform_name = game.get('platform', 'PC')
            
            end_date_text = ""
            if game.get('end_date'):
                try:
                    end_dt = datetime.fromisoformat(game['end_date'].replace('Z', '+00:00'))
                    end_date_text = f"⏰ Available until: {end_dt.strftime('%B %d, %Y')}"
                except:
                    if game['end_date']:
                        end_date_text = f"⏰ {game['end_date']}"
            
            html += f"""
        <div class="game-card">
            <span class="store-badge">{platform_icon} {game['store']}</span>
            <div class="platform-info">Platform: {platform_name}</div>
            """
            
            if game.get('image_url'):
                html += f"""
            <img src="{game['image_url']}" alt="{game['title']}" class="game-image">
            """
            
            html += f"""
            <div class="game-title">{game['title']}</div>
            <div class="price-info">
                <span class="price-original">{game.get('original_price', 'N/A')}</span>
                <span class="price-free">FREE</span>
            </div>
            <div class="game-description">{game['description']}</div>
            """
            
            if end_date_text:
                html += f"""
            <div class="expiry">{end_date_text}</div>
            """
            
            html += f"""
            <a href="{game['game_url']}" class="claim-button">🔗 Claim Now</a>
        </div>
        """
            
            if i < len(games) - 1:
                html += '<div class="divider"></div>'
        
        html += """
        <div class="footer">
            <p>You're receiving this email because you subscribed to Free Game Checker</p>
            <p>Happy gaming! 🎮</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def send_email(self, recipients: List[str], games: List[Dict]):
        """Send fancy HTML email to recipients"""
        
        if not games:
            logger.info("No games to send")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['email_sender']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"🎮 {len(games)} Free Games Available This Week!"
            
            html_content = self.create_html_email(games)
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.config['email_sender'], self.config['email_password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")

def load_config() -> Dict:
    """Load configuration from file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        default_config = {
            'email_sender': 'freegamechecker@gmail.com',
            'email_password': '',
            'schedule_day': 'friday',
            'schedule_time': '09:00',
            'enabled_stores': [
                'Epic Games Store',
                'Steam',
                'GOG',
                'Humble Bundle',
                'Itch.io',
                'Nintendo Switch',
                'Xbox Store',
                'Google Play Games'
            ]
        }
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

def check_and_send_games():
    """Main function to check stores and send emails"""
    logger.info("Starting game check...")
    
    config = load_config()
    db = Database()
    
    # Initialize scrapers
    scrapers = {
        'Epic Games Store': EpicGamesScraper(),
        'Steam': SteamScraper(),
        'GOG': GOGScraper(),
        'Humble Bundle': HumbleBundleScraper(),
        'Itch.io': ItchIOScraper(),
        'Prime Gaming': PrimeGamingScraper(),
        'Google Play Games': GooglePlayScraper(),
        'Nintendo Switch': NintendoSwitchScraper(),
        'Xbox Store': XboxScraper()
    }
    
    # Collect all games
    all_games = []
    for store_name in config.get('enabled_stores', []):
        if store_name in scrapers:
            logger.info(f"Checking {store_name}...")
            games = scrapers[store_name].scrape()
            
            for game in games:
                db.add_game(game)
                all_games.append(game)
    
    # Sort games by platform order
    sorted_games = sorted(all_games, key=lambda x: (
        PLATFORM_ORDER.get(x.get('platform', 'PC'), 99),
        x['store'],
        x['title']
    ))
    
    # Get recipients
    recipients = db.get_recipients()
    
    if not recipients:
        logger.warning("No recipients configured")
        return
    
    if sorted_games:
        email_sender = EmailSender(config)
        email_sender.send_email(recipients, sorted_games)
        logger.info(f"Found and sent {len(sorted_games)} free games")
    else:
        logger.info("No free games found this check")

def run_scheduler():
    """Run the scheduler"""
    config = load_config()
    
    day = config.get('schedule_day', 'friday').lower()
    time_str = config.get('schedule_time', '09:00')
    
    day_map = {
        'monday': schedule.every().monday,
        'tuesday': schedule.every().tuesday,
        'wednesday': schedule.every().wednesday,
        'thursday': schedule.every().thursday,
        'friday': schedule.every().friday,
        'saturday': schedule.every().saturday,
        'sunday': schedule.every().sunday
    }
    
    if day in day_map:
        day_map[day].at(time_str).do(check_and_send_games)
        logger.info(f"Scheduled to run every {day.capitalize()} at {time_str}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check-now':
        check_and_send_games()
    else:
        run_scheduler()
