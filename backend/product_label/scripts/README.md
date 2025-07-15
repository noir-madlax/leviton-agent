# Smart Capability Labeling Scripts

This directory contains standalone scripts for labeling products with smart capability information.

## Scripts Overview

### 1. `label_smart_capability.py`
Main script that labels all products in project `36416581-f0e6-4785-9e65-ef09d0e3e82d` with smart capability labels.

**Features:**
- Retrieves product IDs from `project_extend_data` table
- Gets product titles from `product_wide_table` 
- Uses LLM to assign smart capability labels
- Updates results back to `project_extend_data` table
- Batch processing with configurable batch size
- Retry logic for failed LLM calls
- Progress tracking and detailed logging

**Labels:**
- `Smart`: Connected switches/dimmers with WiFi, Bluetooth, or smart home integration
- `Non-Smart`: Traditional manual switches and dimmers without connectivity
- `Unknown`: Products where smart capability cannot be determined from title
- `N/A`: Products that are not switches or dimmers

### 2. `test_smart_capability.py`
Test script that verifies the labeling functionality with sample product data.

**Features:**
- Tests LLM prompt and validation logic
- Uses sample product titles representing different categories
- Displays results grouped by label for manual verification
- No database operations - pure testing

### 3. `config.py`
Configuration file containing constants and settings for the labeling scripts.

## Usage

### Prerequisites
- Backend environment set up with required dependencies
- Supabase credentials configured
- LLM API access configured in main config

### Running the Test Script
```bash
# Test the labeling functionality with sample data
python -m backend.product_label.scripts.test_smart_capability
```

### Running the Main Script

**Dry Run (recommended first):**
```bash
# Run without making changes to see what would happen
python -m product_label.scripts.label_smart_capability --dry-run
```

**Production Run:**
```bash
# Process all products with default batch size (50)
python -m product_label.scripts.label_smart_capability

# Process with custom batch size
python -m product_label.scripts.label_smart_capability --batch-size 25
```

### Command Line Options

**`label_smart_capability.py`:**
- `--dry-run`: Run without making database changes (for testing)
- `--batch-size N`: Set batch size for processing (default: 50, max: 100)

## Configuration

Edit `config.py` to modify:
- `PROJECT_ID`: Target project ID
- `FIELD_NAME`: Name of the extend field
- `BATCH_SIZE`: Default batch size for processing
- `SMART_CAPABILITY_LABELS`: Label definitions and descriptions
- `MAX_RETRIES`: Maximum LLM retry attempts per batch

## Database Schema

The script works with these tables:

**`project_extend_fields`:**
- Stores field definition and configuration
- Created automatically if doesn't exist

**`project_extend_data`:**
- Stores product label assignments
- Updated with new labels via upsert operation

**`product_wide_table`:**
- Source of product titles for labeling

## Error Handling

The script includes robust error handling:
- LLM validation with retry logic
- Batch-level error recovery
- Detailed logging of successes and failures
- Graceful handling of missing product titles
- Database transaction safety

## Monitoring

The script provides detailed logging including:
- Progress tracking with batch counts
- Success/failure statistics
- Individual product labeling results (in dry-run mode)
- Performance metrics and timing
- Final summary report

## Safety Features

- **Dry run mode**: Test without making changes
- **Batch size limits**: Prevent oversized LLM calls
- **Validation**: Ensure all products are labeled with valid labels
- **Upsert operations**: Safe database updates that won't create duplicates
- **Error isolation**: Failed batches don't stop the entire process 