"""
Configuration constants for smart capability labeling script
"""

# Project and field configuration
LEVITON_PROJECT_ID = "36416581-f0e6-4785-9e65-ef09d0e3e82d"
FIELD_NAME = "smart_capability"
FIELD_TYPE = "product_label"
FIELD_DESCRIPTION = "Categorizes light switches and dimmers by smart/connected capabilities"

# Processing configuration
BATCH_SIZE = 50
MAX_RETRIES = 3
LLM_TEMPERATURE = 0.1

# Smart capability label definitions
SMART_CAPABILITY_LABELS = {
    "Smart": "Connected switches/dimmers with WiFi, Bluetooth, or smart home integration (Alexa, Google, etc.)",
    "Non-Smart": "Traditional manual switches and dimmers without connectivity or smart features",
    "Unknown": "Products where smart capability cannot be determined from the title",
    "N/A": "Products that are not switches or dimmers, or unclear product types"
}

# UI configuration for field
UI_CONFIG = {
    "default": "All",
    "placeholder": "Select smart capability",
    "options": SMART_CAPABILITY_LABELS
}

# Field configuration for project_extend_fields
FIELD_CONFIG = {
    "label_name": FIELD_NAME,
    "label_description": FIELD_DESCRIPTION,
    "instruction": "Smart vs. non-smart switches and dimmers",
    "ui_config": UI_CONFIG
} 