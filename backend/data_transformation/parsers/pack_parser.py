"""Pack parser for extracting pack count from product titles."""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PackParser:
    """Parser for extracting pack count from product titles."""
    
    # Ordered patterns for pack detection - more specific first
    PACK_PATTERNS = [
        # "[50 Pack]" or "(50 Pack)" -> 50
        (r'[\[\(](\d+)\s*pack[\]\)]', lambda x: int(x)),
        # "Pack Of 10" -> 10
        (r'pack\s+of\s+(\d+)', lambda x: int(x)),
        # "50-Pack" or "50 Pack" -> 50
        (r'(\d+)[-\s]*pack(?!\w)', lambda x: int(x)),
        # "24-Pack Case" -> 24
        (r'(\d+)[-\s]*pack\s+case', lambda x: int(x)),
        # "Count of 12" -> 12
        (r'count\s+of\s+(\d+)', lambda x: int(x)),
        # "12 Count" -> 12  
        (r'(\d+)\s+count(?!\w)', lambda x: int(x)),
        # "Set of 6" -> 6
        (r'set\s+of\s+(\d+)', lambda x: int(x)),
        # "6-piece" or "6 piece" -> 6
        (r'(\d+)[-\s]*piece', lambda x: int(x)),
        # "Bundle of 3" -> 3
        (r'bundle\s+of\s+(\d+)', lambda x: int(x)),
    ]
    
    # Single item indicators
    SINGLE_INDICATORS = [
        r'single',
        r'individual', 
        r'1\s*pack',
        r'one\s*pack',
        r'solo',
        r'standalone'
    ]
    
    @classmethod
    def parse_pack_count(cls, title: Optional[str]) -> int:
        """Parse pack count from product title.
        
        Args:
            title: Product title text
            
        Returns:
            Pack count (default 1 if not found)
        """
        if not title:
            return 1
            
        # Normalize title for parsing
        text = title.lower().strip()
        
        # Check for explicit single item indicators first
        for indicator in cls.SINGLE_INDICATORS:
            if re.search(indicator, text):
                return 1
        
        # Try pack detection patterns
        for pattern, converter in cls.PACK_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    count = converter(match.group(1))
                    # Validate reasonable pack sizes
                    if 1 <= count <= 1000:  # Reasonable range
                        logger.debug(f"Parsed pack count {count} from '{title}'")
                        return count
                    else:
                        logger.warning(f"Unreasonable pack count {count} from '{title}', using default")
                        continue
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert pack count from '{match.group(1)}' in '{title}': {e}")
                    continue
        
        # Default to 1 if no pack indicators found
        return 1
    
    @classmethod
    def extract_base_product_name(cls, title: Optional[str]) -> Optional[str]:
        """Extract base product name by removing pack-related information.
        
        Args:
            title: Full product title
            
        Returns:
            Cleaned base product name
        """
        if not title:
            return None
            
        # Remove pack-related phrases
        clean_title = title
        
        # Patterns to remove (keep original case)
        removal_patterns = [
            r'[\[\(]\d+\s*pack[\]\)]',  # [20 Pack], (30 Pack)
            r'\d+[-\s]*pack(?!\w)',      # 50-Pack, 20 Pack
            r'\d+[-\s]*count(?!\w)',     # 12 Count, 6-Count
            r'set\s+of\s+\d+',          # Set of 6
            r'\d+[-\s]*piece',          # 6-piece
            r'bundle\s+of\s+\d+',       # Bundle of 3
            r'single\s*pack',           # Single Pack
            r'individual',              # Individual
        ]
        
        for pattern in removal_patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        # Clean up extra spaces and commas
        clean_title = re.sub(r'\s*,\s*,', ',', clean_title)  # Double commas
        clean_title = re.sub(r'\s+', ' ', clean_title)       # Multiple spaces
        clean_title = clean_title.strip(' ,-')              # Leading/trailing
        
        return clean_title if clean_title else title
    
    @classmethod
    def is_pack_product(cls, title: Optional[str]) -> bool:
        """Check if product title indicates a pack/bundle.
        
        Args:
            title: Product title
            
        Returns:
            True if title indicates pack product
        """
        if not title:
            return False
            
        pack_count = cls.parse_pack_count(title)
        return pack_count > 1 