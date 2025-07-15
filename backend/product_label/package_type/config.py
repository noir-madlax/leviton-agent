"""
Configuration constants for package type labeling
"""

# Project and field configuration
PROJECT_ID = "36416581-f0e6-4785-9e65-ef09d0e3e82d"
FIELD_NAME = "package_type"
FIELD_TYPE = "product_label"
FIELD_DESCRIPTION = "Categorizes products by package type: single, multiple quantities, or bundles"

# Processing configuration
BATCH_SIZE = 25
MAX_RETRIES = 3
LLM_TEMPERATURE = 0.1

# Package type label definitions - keeping Unknown as requested
LABELS = {
    "Single": "Single individual product item",
    "Multiple": "Multiple of the same product (extract quantity and format as Multiple-{number})",
    "Bundle": "Different products bundled together (kits, combos, variety packs)",
    "Unknown": "Cannot determine package type from the title"
}

# UI configuration for field
UI_CONFIG = {
    "default": "All",
    "placeholder": "Select package type",
    "options": LABELS
} 