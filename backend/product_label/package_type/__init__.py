"""
Package type labeling module

This module provides specific functionality for identifying package types
(single, multiple quantities, bundles) of products.
"""

from product_label.package_type.config import *
from product_label.package_type.package_type_stage import PackageTypeStage

__all__ = [
    'PROJECT_ID',
    'FIELD_NAME', 
    'FIELD_TYPE',
    'FIELD_DESCRIPTION',
    'BATCH_SIZE',
    'MAX_RETRIES',
    'LLM_TEMPERATURE',
    'LABELS',
    'UI_CONFIG',
    'PackageTypeStage'
] 