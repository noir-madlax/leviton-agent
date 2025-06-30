"""Price calculator for pack pricing and unit price calculations."""

import logging
from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class PriceCalculator:
    """Calculator for pack pricing and unit price calculations."""
    
    @classmethod
    def calculate_unit_price(cls, total_price: Optional[Decimal], pack_count: int) -> Optional[Decimal]:
        """Calculate unit price from total price and pack count.
        
        Args:
            total_price: Total price for the pack
            pack_count: Number of items in pack
            
        Returns:
            Unit price per item, None if calculation not possible
        """
        if not total_price or pack_count <= 0:
            return None
            
        try:
            unit_price = total_price / pack_count
            # Round to 2 decimal places for currency
            return round(unit_price, 2)
        except (ZeroDivisionError, InvalidOperation) as e:
            logger.warning(f"Failed to calculate unit price: {total_price} / {pack_count}: {e}")
            return None
    
    @classmethod
    def estimate_list_price(cls, current_price: Optional[Decimal], pack_count: int, 
                          title: Optional[str] = None) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Estimate list price and unit price from current price.
        
        For pack products, we assume current_price is the total pack price.
        We estimate the unit list price by dividing by pack count.
        
        Args:
            current_price: Current total price
            pack_count: Number of items in pack  
            title: Product title for context
            
        Returns:
            Tuple of (estimated_list_price_per_unit, unit_price_calculated)
        """
        if not current_price:
            return None, None
            
        if pack_count <= 1:
            # Single item - list price equals current price
            return current_price, current_price
        
        # Pack product - estimate unit list price
        try:
            # Estimate unit price by dividing total price by pack count
            unit_price = current_price / pack_count
            unit_price = round(unit_price, 2)
            
            # For pack products:
            # - list_price_usd should be the unit price  
            # - unit_price_calculated should also be the unit price
            # This matches the pattern in existing product_wide_table data
            
            logger.debug(f"Estimated unit price {unit_price} from pack price {current_price} / {pack_count}")
            return unit_price, unit_price
            
        except (ZeroDivisionError, InvalidOperation) as e:
            logger.warning(f"Failed to estimate unit price from {current_price} / {pack_count}: {e}")
            return None, None
    
    @classmethod  
    def calculate_estimated_revenue(cls, price: Optional[Decimal], monthly_volume: Optional[int]) -> Optional[Decimal]:
        """Calculate estimated monthly revenue.
        
        Args:
            price: Product price (total pack price)
            monthly_volume: Monthly sales volume
            
        Returns:
            Estimated monthly revenue
        """
        if not price or not monthly_volume or monthly_volume <= 0:
            return None
            
        try:
            revenue = price * monthly_volume
            return round(revenue, 2)
        except (TypeError, InvalidOperation) as e:
            logger.warning(f"Failed to calculate revenue: {price} * {monthly_volume}: {e}")
            return None
    
    @classmethod
    def validate_price(cls, price: Optional[Decimal]) -> bool:
        """Validate that price is reasonable.
        
        Args:
            price: Price to validate
            
        Returns:
            True if price seems reasonable
        """
        if not price:
            return False
            
        # Check for reasonable price range (0.01 to 10,000)
        if not (Decimal('0.01') <= price <= Decimal('10000')):
            logger.warning(f"Price {price} outside reasonable range")
            return False
            
        return True
    
    @classmethod
    def safe_decimal_conversion(cls, value: Optional[str]) -> Optional[Decimal]:
        """Safely convert string to Decimal.
        
        Args:  
            value: String value to convert
            
        Returns:
            Decimal value or None if conversion fails
        """
        if not value:
            return None
            
        try:
            # Clean the string (remove currency symbols, etc.)
            clean_value = str(value).strip().replace('$', '').replace(',', '')
            return Decimal(clean_value)
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Failed to convert '{value}' to Decimal: {e}")
            return None 