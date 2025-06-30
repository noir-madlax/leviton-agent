"""Sales volume parser for extracting monthly sales from recent_sales text."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SalesVolumeParser:
    """Parser for extracting monthly sales volume from Amazon recent_sales text."""
    
    # Ordered patterns - more specific patterns first
    PATTERNS = [
        # "1.5K bought in past month" -> 1500 (decimal K format, most specific)
        (r'(\d*\.?\d+)k\+?\s+bought\s+in\s+past\s+month', lambda x: int(float(x) * 1000)),
        # "20K+ bought in past month" -> 20000
        (r'(\d+)k\+?\s+bought\s+in\s+past\s+month', lambda x: int(x) * 1000),
        # "500+ bought in past month" -> 500  
        (r'(\d+)\+?\s+bought\s+in\s+past\s+month', lambda x: int(x)),
        # "1.5K bought" -> 1500 (fallback decimal K without "in past month")
        (r'(\d*\.?\d+)k\+?\s+bought', lambda x: int(float(x) * 1000)),
        # "2K+ bought" -> 2000 (fallback without "in past month")
        (r'(\d+)k\+?\s+bought', lambda x: int(x) * 1000),
        # "100+ bought" -> 100 (fallback without "in past month")  
        (r'(\d+)\+?\s+bought', lambda x: int(x)),
    ]
    
    @classmethod
    def parse(cls, recent_sales: Optional[str]) -> int:
        """Parse recent sales text to extract monthly sales volume.
        
        Args:
            recent_sales: Text like "3K+ bought in past month"
            
        Returns:
            Monthly sales volume as integer, 0 if parsing fails
        """
        if not recent_sales:
            return 0
            
        # Normalize text for parsing
        text = recent_sales.lower().strip()
        
        # Try each pattern in order
        for pattern, converter in cls.PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    volume = converter(match.group(1))
                    logger.debug(f"Parsed '{recent_sales}' -> {volume}")
                    return volume
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert '{match.group(1)}' from '{recent_sales}': {e}")
                    continue
        
        # Log unparsed text for improvement
        logger.warning(f"Could not parse sales volume from: '{recent_sales}'")
        return 0
    
    @classmethod
    def validate_result(cls, result: int, original_text: str) -> bool:
        """Validate that parsed result is reasonable.
        
        Args:
            result: Parsed sales volume
            original_text: Original text
            
        Returns:
            True if result seems reasonable
        """
        if result < 0:
            return False
            
        # Check for unreasonably high values (> 1M per month)
        if result > 1_000_000:
            logger.warning(f"Suspiciously high sales volume {result} from '{original_text}'")
            return False
            
        return True 