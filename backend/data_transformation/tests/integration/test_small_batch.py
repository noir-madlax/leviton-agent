"""Small batch testing script for data transformation."""

import logging
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data_transformation.services.transformation_service import DataTransformationService
from data_transformation.models import TransformationConfig
from data_transformation.parsers import SalesVolumeParser, PackParser, PriceCalculator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_parsers():
    """Test individual parsers with known examples."""
    logger.info("=== Testing Individual Parsers ===")
    
    # Test sales volume parser
    test_sales = [
        ("6K+ bought in past month", 6000),
        ("20K+ bought in past month", 20000),
        ("700+ bought in past month", 700),
        ("5K+ bought in past month", 5000),
        ("1.5K bought in past month", 1500),
        ("", 0),
        (None, 0)
    ]
    
    logger.info("Testing SalesVolumeParser:")
    for text, expected in test_sales:
        result = SalesVolumeParser.parse(text)
        status = "✅" if result == expected else "❌"
        logger.info(f"  {status} '{text}' → {result} (expected {expected})")
    
    # Test pack parser
    test_packs = [
        ("Cra-Z-Art Classic Super Washable Markers, Broad Tip, Assorted Barrel, Assorted Ink, Pack Of 10 Markers", 10),
        ("Play-Doh Modeling Compound 24-Pack Case of Colors", 24),
        ("[50 Pack] CML Decorator Wall Light Switch", 50),
        ("Single Pole Switch", 1),
        ("Leviton Dimmer Switch", 1),
        ("(12-Pack) UNIELE Ultra Slim Dimmer Switch", 12)
    ]
    
    logger.info("\nTesting PackParser:")
    for title, expected in test_packs:
        result = PackParser.parse_pack_count(title)
        status = "✅" if result == expected else "❌"
        logger.info(f"  {status} pack_count={result} (expected {expected}) for '{title[:60]}...'")
    
    # Test price calculator
    logger.info("\nTesting PriceCalculator:")
    test_prices = [
        (69.34, 50, 1.39),  # Pack product
        (42.99, 1, 42.99),  # Single product
        (21.99, 24, 0.92),  # Pack product
    ]
    
    for total_price, pack_count, expected_unit in test_prices:
        list_price, unit_price = PriceCalculator.estimate_list_price(
            PriceCalculator.safe_decimal_conversion(str(total_price)), 
            pack_count
        )
        status = "✅" if abs(float(unit_price or 0) - expected_unit) < 0.01 else "❌"
        logger.info(f"  {status} ${total_price} / {pack_count} → unit=${unit_price} (expected ${expected_unit})")


def test_small_batch_transformation():
    """Test transformation with a small batch of real data."""
    logger.info("\n=== Testing Small Batch Transformation ===")
    
    # Create test configuration
    config = TransformationConfig(
        batch_size=10,
        skip_existing=False,  # Don't skip for testing
        validate_calculations=True,
        dry_run=True,  # Don't actually write to database
        log_level="DEBUG"
    )
    
    service = DataTransformationService(config)
    
    # Test transformation
    result = service.transform_batch(limit=5)  # Only test 5 records
    
    logger.info(f"Transformation Results:")
    logger.info(f"  Success: {result.success}")
    logger.info(f"  Processed: {result.processed_count}")
    logger.info(f"  Skipped: {result.skipped_count}")
    logger.info(f"  Errors: {result.error_count}")
    logger.info(f"  Duration: {result.duration_seconds:.2f}s")
    logger.info(f"  Summary: {result.summary}")
    
    if result.errors:
        logger.warning(f"Errors encountered:")
        for error in result.errors[:5]:  # Show first 5 errors
            logger.warning(f"  - {error}")
    
    # Calculate success rate
    total_attempted = result.processed_count + result.error_count
    if total_attempted > 0:
        success_rate = result.processed_count / total_attempted * 100
        logger.info(f"  Success Rate: {success_rate:.1f}%")


def test_field_mapping():
    """Test field mapping completeness."""
    logger.info("\n=== Testing Field Mapping ===")
    
    # Sample record structure based on amazon_products
    sample_record = {
        'platform_id': 'B123456789',
        'title': 'Test [20 Pack] Light Switch',
        'brand': 'Test Brand',
        'model_number': 'TEST-123',
        'category': 'Light Switches',
        'image_url': 'https://example.com/image.jpg',
        'product_url': 'https://example.com/product',
        'availability': 'In Stock',
        'recent_sales': '1K+ bought in past month',
        'is_bestseller': 'Yes',
        'unit_price': '$2.50',
        'price_usd': '50.00',
        'rating': '4.5',
        'reviews_count': '1234',
        'position': 1,
        'extract_date': '2025-01-18'
    }
    
    service = DataTransformationService()
    transformed = service._transform_single_product(sample_record)
    
    if transformed:
        logger.info("✅ Field mapping successful")
        logger.info("Transformed fields:")
        for key, value in transformed.items():
            logger.info(f"  {key}: {value}")
        
        # Check key calculations
        expected_sales = 1000  # 1K+
        expected_revenue = 50.00 * 1000  # price * volume
        expected_pack = 20  # [20 Pack]
        expected_unit_price = 50.00 / 20  # 2.50
        
        checks = [
            ("monthly_sales_volume", transformed.get('monthly_sales_volume'), expected_sales),
            ("estimated_revenue", float(transformed.get('estimated_revenue') or 0), expected_revenue),
            ("pack_count", transformed.get('pack_count'), expected_pack),
            ("unit_price_calculated", float(transformed.get('unit_price_calculated') or 0), expected_unit_price)
        ]
        
        logger.info("\nCalculation checks:")
        for field, actual, expected in checks:
            if isinstance(expected, float):
                status = "✅" if abs(actual - expected) < 0.01 else "❌"
            else:
                status = "✅" if actual == expected else "❌"
            logger.info(f"  {status} {field}: {actual} (expected {expected})")
    else:
        logger.error("❌ Field mapping failed")


def test_data_quality():
    """Test data quality validation."""
    logger.info("\n=== Testing Data Quality ===")
    
    from data_transformation.validators.data_validator import DataValidator
    
    validator = DataValidator()
    
    # Test valid data
    valid_data = {
        'platform_id': 'B123456789',
        'source': 'amazon',
        'position': 1,
        'price_usd': 29.99,
        'monthly_sales_volume': 500,
        'estimated_revenue': 14995.00,
        'pack_count': 1,
        'unit_price_calculated': 29.99
    }
    
    result = validator.validate_product_data(valid_data)
    logger.info(f"✅ Valid data validation: {result}")
    
    # Test invalid data
    invalid_data = {
        'platform_id': 'B123456789',
        'source': 'amazon',
        'position': 1,
        'price_usd': -10.00,  # Invalid negative price
        'monthly_sales_volume': 500,
        'estimated_revenue': 5000.00,  # Doesn't match calculation
        'pack_count': 0,  # Invalid pack count
        'rating': 10  # Invalid rating > 5
    }
    
    result = validator.validate_product_data(invalid_data)
    logger.info(f"❌ Invalid data validation (should be False): {result}")


def main():
    """Run all tests."""
    logger.info("🧪 Starting Data Transformation Tests")
    logger.info("=" * 50)
    
    try:
        test_parsers()
        test_field_mapping()
        test_data_quality()
        test_small_batch_transformation()
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 