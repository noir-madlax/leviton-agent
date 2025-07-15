# Product Labeling System

A modular and extensible system for labeling products using LLM-based classification with specialized stages for different labeling types.

## Overview

This system provides a generic framework for creating product labeling services with extensible validation and prompt building. Currently supports:
- **Smart Capability Labeling**: Categorizes products by smart/connected features
- **Package Type Labeling**: Identifies single items, multiple quantities, and bundles with dynamic number extraction

## Architecture

### Base Abstractions
- **BaseService**: Handles database operations, batch processing, and orchestration
- **BaseStage**: Generic LLM processing with extensible validation and prompt building
- **Models**: Shared data structures for configuration, results, and statistics

### Specialized Stages
The system supports labeling-type specific stages that extend BaseStage:
- **PackageTypeStage**: Handles dynamic `Multiple-{number}` format validation and consistent examples
- **BaseStage**: Generic exact-match validation for standard labeling types

### Labeling Services
Each labeling service consists of:
- **Configuration**: Labels, field settings, and processing parameters
- **Stage**: Optional specialized stage with custom validation/prompt logic
- **Prompt Template**: LLM instructions for the specific labeling task
- **Sample Data**: Test products for development and validation

## Quick Start

### Smart Capability Labeling
```bash
# Test with sample data
python -m backend.product_label.base.test_runner smart_capability

# Label 10 products (dry run)
python -m backend.product_label.base.cli_runner smart_capability --dry-run --sample-size 10

# Full production run
python -m backend.product_label.base.cli_runner smart_capability
```

### Package Type Labeling
```bash
# Test with sample data
python -m backend.product_label.base.test_runner package_type

# Label 10 products (dry run)
python -m backend.product_label.base.cli_runner package_type --dry-run --sample-size 10

# Full production run
python -m backend.product_label.base.cli_runner package_type
```

## Command Line Options

### CLI Runner
- `--dry-run`: Run without making database changes
- `--sample-size N`: Limit processing to N products
- `--batch-size N`: Set batch size (default: 25)
- `--max-retries N`: Maximum LLM retry attempts (default: 3)

### Examples
```bash
# Test 5 products with custom batch size
python -m backend.product_label.base.cli_runner smart_capability --dry-run --sample-size 5 --batch-size 10

# Production run with smaller batches
python -m backend.product_label.base.cli_runner package_type --batch-size 15
```

## Labels

### Smart Capability Labels
- **Smart**: Connected switches/dimmers with WiFi, Bluetooth, or smart home integration
- **Non-Smart**: Traditional manual switches and dimmers without connectivity
- **Unknown**: Products where smart capability cannot be determined
- **N/A**: Products that are not switches or dimmers

### Package Type Labels
- **Single**: Single individual product item
- **Multiple-{number}**: Multiple of the same product with dynamic quantity extraction (e.g., Multiple-2, Multiple-6, Multiple-12)
- **Bundle**: Different products bundled together (kits, combos, variety packs)
- **Unknown**: Cannot determine package type from title

#### Dynamic Number Extraction
The package type system automatically extracts quantities from product titles:
- `"2-Pack"` → `"Multiple-2"`
- `"3-Pack"` → `"Multiple-3"`
- `"Pair"` → `"Multiple-2"`
- `"8 Count"` → `"Multiple-8"`
- `"12-Pack"` → `"Multiple-12"`
- No limit on quantity - can handle any positive integer

## Output

The system provides:
1. **Full Prompt Display**: Shows the complete LLM prompt for the first batch
2. **Results Table**: Formatted table showing product titles and assigned labels
3. **Summary Statistics**: Success rates, timing, and batch information
4. **Manual Inspection**: Sample results for quality verification

### Example Output
```
Index Product_ID                                Title              Label  Batch
    0        857  Leviton Decora Smart Dimmer Switch...       Smart      1
    1        200  Philips Hue Smart Wireless Dimmer...       Smart      1
    2        853  Lutron 3-Pack Caseta Smart Dimmer...  Multiple-3      1
    3        862  LIDER Dual Rocker Light Switch...      Non-Smart      1
    4        851  DEWENWILS 6-Pack Outdoor Dimmer...   Multiple-6      1

📋 Results Summary by Label:
   Smart: 2 products (indices: [0, 1])
   Multiple-3: 1 products (indices: [2])
   Multiple-6: 1 products (indices: [4])
   Non-Smart: 1 products (indices: [3])
```

## Adding New Labeling Services

### Basic Service (Generic Validation)
To add a new labeling service with standard exact-match validation:

1. **Create directory structure**:
   ```
   backend/product_label/brand_classification/
   ├── __init__.py
   ├── config.py
   ├── sample_data.py
   └── prompts/
       └── brand_classification_prompt_v0.txt
   ```

2. **Configure labels in config.py**:
   ```python
   PROJECT_ID = "your-project-id"
   FIELD_NAME = "brand_classification"
   FIELD_DESCRIPTION = "Categorizes products by brand"
   LABELS = {
       "Leviton": "Leviton brand products",
       "Lutron": "Lutron brand products", 
       "Other": "Other brands",
       "Unknown": "Cannot determine brand"
   }
   ```

3. **Run the new service**:
   ```bash
   python -m backend.product_label.base.cli_runner brand_classification --dry-run
   ```

### Advanced Service (Custom Validation)
For services requiring custom validation or prompt building:

1. **Create specialized stage**:
   ```python
   # brand_classification/brand_stage.py
   from backend.product_label.base.base_stage import BaseStage
   
   class BrandStage(BaseStage):
       def _is_valid_label(self, label: str, valid_labels: set) -> bool:
           # Custom validation logic
           return super()._is_valid_label(label, valid_labels)
           
       def _build_output_format_example(self, available_labels, num_products):
           # Custom example generation
           return super()._build_output_format_example(available_labels, num_products)
   ```

2. **Update __init__.py**:
   ```python
   from .brand_stage import BrandStage
   ```

3. **Add to CLI/test runners**:
   ```python
   # In cli_runner.py create_stage function
   elif labeling_type == "brand_classification":
       from backend.product_label.brand_classification import BrandStage
       return BrandStage(prompt_template_path, max_retries)
   ```

## Specialized Stages

### PackageTypeStage Features
- **Dynamic Validation**: Accepts both exact matches and `Multiple-{number}` format
- **Consistent Examples**: Shows realistic `Multiple-2`, `Multiple-3` examples in prompts
- **Smart Error Messages**: Provides package-type specific validation feedback
- **Number Extraction**: Validates positive integers in `Multiple-{number}` format

### Creating Custom Stages
Override these methods in your specialized stage:

```python
def _is_valid_label(self, label: str, valid_labels: set) -> bool:
    """Custom label validation logic"""
    
def _build_output_format_example(self, available_labels, num_products) -> str:
    """Custom example generation for prompts"""
    
def _validate_response(self, response: str, context: LabelingContext) -> ValidationResult:
    """Complete custom validation override"""
```

## Database Schema

### Tables Used
- **project_extend_fields**: Stores field definitions and UI configuration
- **project_extend_data**: Stores product label assignments
- **product_wide_table**: Source of product titles for labeling

### Field Creation
Fields are automatically created in `project_extend_fields` with:
- Proper UI configuration for filtering
- Label descriptions and options
- Integration with existing project structure

## Error Handling

The system includes robust error handling:
- **LLM Validation**: Ensures all products get valid labels (including dynamic formats)
- **Retry Logic**: Automatic retries with error details
- **Batch Recovery**: Failed batches don't stop the entire process
- **Database Safety**: Upsert operations prevent duplicates
- **Stage-Specific Errors**: Custom validation messages for specialized stages

## Performance

- **Default batch size**: 25 (optimized for LLM context limits)
- **Concurrent processing**: Handled by global rate limiter
- **Memory efficient**: Processes products in chunks
- **Fast testing**: Sample sizes for development
- **Extensible validation**: Minimal overhead for custom stages

## Safety Features

- **Dry run mode**: Test without making changes
- **Sample size limits**: Process subset for testing
- **Validation**: Comprehensive response checking with custom rules
- **Logging**: Detailed progress and error reporting
- **Stage isolation**: Labeling-specific logic contained in specialized stages

## Monitoring

Each run provides:
- Total products processed
- Success/failure counts
- Processing duration
- Batch-level statistics
- Individual labeling results (in dry-run mode)
- Stage-specific validation metrics 