"""Data validator for ensuring transformation quality."""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class DataValidator:
    """Validator for transformed product data."""
    
    # Required fields for product_wide_table
    REQUIRED_FIELDS = [
        'platform_id',
        'source',
        'position'
    ]
    
    # Fields that should be numeric when present
    NUMERIC_FIELDS = [
        'price_usd',
        'list_price_usd', 
        'rating',
        'reviews_count',
        'estimated_revenue',
        'unit_price_calculated',
        'unit_price_numeric'
    ]
    
    # Fields that should be integers when present
    INTEGER_FIELDS = [
        'monthly_sales_volume',
        'pack_count',
        'position'
    ]
    
    def validate_product_data(self, data: Dict[str, Any]) -> bool:
        """Validate a single product data record.
        
        Args:
            data: Transformed product data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not self._validate_required_fields(data):
                return False
            
            # Check data types
            if not self._validate_data_types(data):
                return False
            
            # Check business logic
            if not self._validate_business_logic(data):
                return False
            
            # Check calculations
            if not self._validate_calculations(data):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error for {data.get('platform_id', 'unknown')}: {e}")
            return False
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> bool:
        """Validate that required fields are present and non-empty.
        
        Args:
            data: Product data to validate
            
        Returns:
            True if all required fields are valid
        """
        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
            
            # Check for empty strings
            if isinstance(data[field], str) and not data[field].strip():
                logger.warning(f"Empty required field: {field}")
                return False
        
        return True
    
    def _validate_data_types(self, data: Dict[str, Any]) -> bool:
        """Validate data types for numeric fields.
        
        Args:
            data: Product data to validate
            
        Returns:
            True if data types are correct
        """
        # Check numeric fields
        for field in self.NUMERIC_FIELDS:
            value = data.get(field)
            if value is not None and not isinstance(value, (int, float, Decimal)):
                logger.warning(f"Invalid numeric type for {field}: {type(value)}")
                return False
        
        # Check integer fields
        for field in self.INTEGER_FIELDS:
            value = data.get(field)
            if value is not None and not isinstance(value, int):
                logger.warning(f"Invalid integer type for {field}: {type(value)}")
                return False
        
        return True
    
    def _validate_business_logic(self, data: Dict[str, Any]) -> bool:
        """Validate business logic constraints.
        
        Args:
            data: Product data to validate
            
        Returns:
            True if business logic is valid
        """
        # Price validation
        price_usd = data.get('price_usd')
        if price_usd is not None:
            if price_usd < 0:
                logger.warning(f"Negative price: {price_usd}")
                return False
            if price_usd > Decimal('10000'):
                logger.warning(f"Suspiciously high price: {price_usd}")
                return False
        
        # Sales volume validation
        monthly_sales = data.get('monthly_sales_volume')
        if monthly_sales is not None:
            if monthly_sales < 0:
                logger.warning(f"Negative sales volume: {monthly_sales}")
                return False
            if monthly_sales > 1_000_000:
                logger.warning(f"Suspiciously high sales volume: {monthly_sales}")
                return False
        
        # Pack count validation
        pack_count = data.get('pack_count', 1)
        if pack_count < 1 or pack_count > 1000:
            logger.warning(f"Invalid pack count: {pack_count}")
            return False
        
        # Rating validation
        rating = data.get('rating')
        if rating is not None:
            if rating < 0 or rating > 5:
                logger.warning(f"Invalid rating: {rating}")
                return False
        
        return True
    
    def _validate_calculations(self, data: Dict[str, Any]) -> bool:
        """Validate calculated fields are consistent.
        
        Args:
            data: Product data to validate
            
        Returns:
            True if calculations are consistent
        """
        # Validate revenue calculation
        price = data.get('price_usd')
        volume = data.get('monthly_sales_volume')
        revenue = data.get('estimated_revenue')
        
        if price and volume and revenue:
            expected_revenue = price * volume
            # Allow small rounding differences
            if abs(float(revenue) - float(expected_revenue)) > 0.01:
                logger.warning(f"Revenue calculation mismatch: {revenue} != {price} * {volume}")
                return False
        
        # Validate unit price consistency
        unit_calc = data.get('unit_price_calculated')
        unit_numeric = data.get('unit_price_numeric')
        
        if unit_calc and unit_numeric:
            if abs(float(unit_calc) - float(unit_numeric)) > 0.01:
                logger.warning(f"Unit price mismatch: {unit_calc} != {unit_numeric}")
                return False
        
        # Validate pack pricing logic for pack products
        pack_count = data.get('pack_count', 1)
        list_price = data.get('list_price_usd')
        current_price = data.get('price_usd')
        
        if pack_count > 1 and list_price and current_price:
            # For pack products, current price should generally be higher than unit price
            if current_price < list_price:
                logger.warning(f"Pack price ({current_price}) less than unit price ({list_price}) for pack of {pack_count}")
                # This might be valid (bulk discount), so just warn, don't fail
        
        return True
    
    def validate_batch(self, batch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of product data.
        
        Args:
            batch_data: List of product data records
            
        Returns:
            Validation summary with statistics
        """
        valid_count = 0
        invalid_count = 0
        errors = []
        
        for i, data in enumerate(batch_data):
            if self.validate_product_data(data):
                valid_count += 1
            else:
                invalid_count += 1
                platform_id = data.get('platform_id', f'record_{i}')
                errors.append(f"Validation failed for {platform_id}")
        
        total_count = len(batch_data)
        success_rate = round(valid_count / total_count * 100, 2) if total_count > 0 else 0
        
        return {
            'total_records': total_count,
            'valid_records': valid_count,
            'invalid_records': invalid_count,
            'success_rate': success_rate,
            'errors': errors
        } 