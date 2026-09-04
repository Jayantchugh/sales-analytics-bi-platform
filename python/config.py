"""Configuration constants for the Sales Analytics platform."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SQL_DIR = PROJECT_ROOT / "sql"
DB_PATH = DATA_DIR / "sales_analytics.db"

NUM_SALES_RECORDS = 250_000
NUM_PRODUCTS = 500
NUM_CUSTOMERS = 10_000
NUM_REGIONS = 12
START_DATE = "2022-01-01"
END_DATE = "2025-08-31"

REGIONS = [
    ("North America East", "USA", "East"),
    ("North America West", "USA", "West"),
    ("North America Central", "Canada", "Central"),
    ("Europe UK", "UK", "EMEA"),
    ("Europe Germany", "Germany", "EMEA"),
    ("Europe France", "France", "EMEA"),
    ("Asia Pacific Japan", "Japan", "APAC"),
    ("Asia Pacific Australia", "Australia", "APAC"),
    ("Asia Pacific India", "India", "APAC"),
    ("Latin America Brazil", "Brazil", "LATAM"),
    ("Latin America Mexico", "Mexico", "LATAM"),
    ("Middle East UAE", "UAE", "MEA"),
]

CATEGORIES = {
    "Electronics": ["Laptops", "Phones", "Tablets", "Accessories", "Audio"],
    "Home & Garden": ["Furniture", "Decor", "Kitchen", "Outdoor", "Lighting"],
    "Clothing": ["Men", "Women", "Kids", "Footwear", "Accessories"],
    "Sports": ["Equipment", "Apparel", "Outdoor", "Fitness", "Team Sports"],
    "Beauty": ["Skincare", "Makeup", "Haircare", "Fragrance", "Tools"],
}

SEGMENTS = ["Enterprise", "SMB", "Consumer", "Government"]
INDUSTRIES = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education", "Energy"]
CHANNELS = ["Online", "Retail", "Partner", "Direct"]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
