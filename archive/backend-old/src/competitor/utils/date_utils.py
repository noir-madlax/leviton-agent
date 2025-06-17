"""
Date parsing and validation utilities.

Provides:
- Date parsing from various formats
- Date validation and range checking
- Date filtering utilities
"""

from datetime import datetime, timedelta
from typing import Optional, List


class DateParser:
    """Utility class for parsing and validating dates"""
    
    def __init__(self, min_year: int = 2010, max_year: Optional[int] = None):
        """
        Initialize date parser with validation bounds
        
        Args:
            min_year: Minimum acceptable year
            max_year: Maximum acceptable year (defaults to current year)
        """
        self.min_year = min_year
        self.max_year = max_year or datetime.now().year
        
        # Common date formats to try
        self.date_formats = [
            "%B %d, %Y",      # "May 23, 2025"
            "%b %d, %Y",      # "May 23, 2025" (abbreviated month)
            "%m/%d/%Y",       # "05/23/2025"
            "%Y-%m-%d",       # "2025-05-23"
            "%d %B %Y",       # "23 May 2025"
            "%d %b %Y",       # "23 May 2025" (abbreviated month)
            "%Y-%m-%dT%H:%M:%S",  # ISO format
            "%Y-%m-%d %H:%M:%S",  # SQL format
        ]
    
    def parse_review_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse review date string to datetime object.
        Handles Amazon review format: "Reviewed in the United States on May 23, 2025"
        
        Args:
            date_str: Date string from review
        
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        # Extract date part from Amazon format: "Reviewed in [Country] on [Date]"
        if " on " in date_str:
            date_part = date_str.split(" on ")[-1].strip()
        else:
            date_part = date_str.strip()
        
        return self.parse_date(date_part)
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string using multiple format attempts
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        date_part = date_str.strip()
        
        # Try various date formats
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_part, fmt)
            except ValueError:
                continue
        
        return None
    
    def is_valid_date(self, date_str: str) -> bool:
        """
        Validate if a date string is parseable and within acceptable bounds
        
        Args:
            date_str: Date string to validate
        
        Returns:
            True if date is valid and within bounds
        """
        parsed_date = self.parse_date(date_str)
        if not parsed_date:
            return False
        
        # Check year bounds
        return self.min_year <= parsed_date.year <= self.max_year
    
    def is_valid_review_date(self, review_date_str: str) -> bool:
        """
        Validate review date string (handles Amazon format)
        
        Args:
            review_date_str: Review date string
        
        Returns:
            True if date is valid and within bounds
        """
        parsed_date = self.parse_review_date(review_date_str)
        if not parsed_date:
            return False
        
        # Check year bounds
        return self.min_year <= parsed_date.year <= self.max_year
    
    def filter_by_date_range(self, items: List[dict], date_field: str, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           is_review_format: bool = False) -> List[dict]:
        """
        Filter items by date range
        
        Args:
            items: List of items with date fields
            date_field: Name of the date field in each item
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            is_review_format: Whether to use review date parsing
            
        Returns:
            Filtered list of items within date range
        """
        filtered_items = []
        
        for item in items:
            date_str = item.get(date_field, "")
            
            if is_review_format:
                parsed_date = self.parse_review_date(date_str)
            else:
                parsed_date = self.parse_date(date_str)
            
            if not parsed_date:
                continue
            
            # Check date range
            if start_date and parsed_date < start_date:
                continue
            if end_date and parsed_date > end_date:
                continue
            
            filtered_items.append(item)
        
        return filtered_items
    
    def get_cutoff_date(self, months_back: int) -> datetime:
        """
        Get cutoff date for filtering (current date minus specified months)
        
        Args:
            months_back: Number of months to go back
            
        Returns:
            Cutoff datetime
        """
        days_back = months_back * 30  # Approximation
        return datetime.now() - timedelta(days=days_back)


# Convenience functions for common use cases
def parse_review_date(date_str: str, min_year: int = 2010) -> Optional[datetime]:
    """
    Parse review date string with default settings
    
    Args:
        date_str: Review date string
        min_year: Minimum acceptable year
        
    Returns:
        Parsed datetime or None
    """
    parser = DateParser(min_year=min_year)
    return parser.parse_review_date(date_str)


def is_valid_review_date(review_date_str: str, min_year: int = 2010, 
                        max_year: Optional[int] = None) -> bool:
    """
    Validate review date with default settings
    
    Args:
        review_date_str: Review date string
        min_year: Minimum acceptable year
        max_year: Maximum acceptable year
        
    Returns:
        True if valid
    """
    parser = DateParser(min_year=min_year, max_year=max_year)
    return parser.is_valid_review_date(review_date_str)


def filter_reviews_by_age(reviews: List[dict], months_back: int = 6, 
                         date_field: str = "date") -> List[dict]:
    """
    Filter reviews to only include those within specified months
    
    Args:
        reviews: List of review dictionaries
        months_back: Number of months to include
        date_field: Name of the date field
        
    Returns:
        Filtered reviews
    """
    parser = DateParser()
    cutoff_date = parser.get_cutoff_date(months_back)
    return parser.filter_by_date_range(reviews, date_field, start_date=cutoff_date, 
                                     is_review_format=True) 