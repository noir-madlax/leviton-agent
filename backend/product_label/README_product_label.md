# Backend Product Label Module - Implementation Plan

Based on the analysis of the existing `product_segment` module structure and database patterns, here's a detailed plan for creating the new `backend/product_label` module that leverages existing Supabase tables.

## 1. Module Overview

The `product_label` module will provide a service to assign discrete labels to products based on their titles using LLM processing. It follows a two-stage LLM approach:

1. **Template Expansion**: LLM fills a reusable prompt template with label metadata and display-friendly definitions
2. **Batch Processing**: LLM processes product batches using the expanded template

## 2. Module Structure

```
backend/product_label/
├── __init__.py
├── api.py                              # FastAPI router and endpoints
├── models.py                           # Pydantic models
├── config.py                           # Configuration constants
├── llm/
│   ├── __init__.py
│   ├── label_expansion_stage.py        # Template expansion LLM stage
│   ├── label_assignment_stage.py       # Product labeling LLM stage
│   └── prompts/
│       ├── label_expansion_prompt_v0.txt
│       └── label_assignment_prompt_v0.txt
├── repositories/
│   ├── __init__.py
│   ├── extend_field_repository.py      # Uses project_extend_fields table
│   └── extend_data_repository.py       # Uses project_extend_data table
├── services/
│   ├── __init__.py
│   └── db_product_labeling_service.py
├── sql/
│   └── 001_create_product_label_llm_tracking.sql
└── tests/
    ├── __init__.py
    ├── unit/
    ├── integration/
    └── llm/
```

## 3. Database Schema

### 3.1 Existing Tables Usage

**Using `project_extend_fields` table for label metadata:**
- Create new field with `field_type = 'product_label'`
- Store label configuration in `field_config` JSON field
- `field_name` stores the label name (e.g., "smart_capability")

**Using `project_extend_data` table for assignments:**
- Store product label assignments using existing structure
- `field_id` references the label field in `project_extend_fields`
- `product_id` references products
- `value` stores the assigned label value

### 3.2 New LLM Tracking Table

```sql
-- LLM interaction and progress tracking
CREATE TABLE product_label_llm_interactions (
    id              BIGSERIAL PRIMARY KEY,
    field_id        BIGINT REFERENCES project_extend_fields(id) ON DELETE CASCADE,
    stage           VARCHAR(20) NOT NULL, -- 'expansion' or 'assignment'
    total_products  INT DEFAULT 0,
    completed_products INT DEFAULT 0,
    file_path       TEXT UNIQUE,
    cache_key       VARCHAR(32),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### 3.3 Label Configuration Structure

The `field_config` in `project_extend_fields` will store:

```json
{
  "label_name": "smart_capability",
  "label_description": "Categorizes light switches and dimmers by smart/connected capabilities",
  "instruction": "Smart vs. non-smart switches and dimmers",
  "ui_config": {
    "default": "All",
    "placeholder": "Select product type",
    "options": {
      "Smart": "Connected switches/dimmers with WiFi, Bluetooth, or smart home integration (Alexa, Google, etc.)",
      "Non-Smart": "Traditional manual switches and dimmers without connectivity or smart features",
      "Unknown": "Products where smart capability cannot be determined from the title",
      "N/A": "Products that are not switches or dimmers, or unclear product types"
    }
  }
}
```

## 4. API Design

### 4.1 Request/Response Models

```python
# models.py
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Dict
from enum import Enum

class LabelingStage(str, Enum):
    INIT = "init"
    EXPANSION = "expansion"
    ASSIGNMENT = "assignment"
    COMPLETED = "completed"
    FAILED = "failed"

class CreateLabelingRunRequest(BaseModel):
    project_id: str
    category: str
    product_ids: List[Union[int, str]]
    instruction: str = Field(..., description="Natural language cue for LLM labeling")
    field_name: str = Field(..., description="Name for the label field")

class LabelOption(BaseModel):
    value: str
    definition: str

class LabelUIConfig(BaseModel):
    default: str = "All"
    placeholder: str
    options: Dict[str, str]  # {"Smart": "definition", "Non-Smart": "definition", ...}

class ProductLabelField(BaseModel):
    id: int
    field_name: str
    label_description: str
    instruction: str
    ui_config: LabelUIConfig
    total_products: int
    completed_products: int
    stage: LabelingStage
```

### 4.2 API Endpoint

```python
# api.py
@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_and_start_labeling_run(
    request_body: CreateLabelingRunRequest,
    background_tasks: BackgroundTasks,
    service: DatabaseProductLabelingService = Depends(_get_service),
) -> Response:
    """Create and asynchronously execute a product labeling run."""
    
    field_id = await service.create_label_field(request_body)
    background_tasks.add_task(service.execute_labeling, field_id)
    
    headers = {"Location": f"/product-label/{field_id}"}
    return Response(status_code=status.HTTP_202_ACCEPTED, headers=headers)
```

## 5. LLM Processing Stages

### 5.1 Stage 1: Template Expansion

**Purpose**: Use LLM to create display-friendly label options with definitions

**Input**: 
- `instruction`: "Smart vs. non-smart switches and dimmers"
- `category`: "Light Switches & Dimmers"

**Expected Output**:
```json
{
  "label_name": "smart_capability",
  "label_description": "Categorizes light switches and dimmers by smart/connected capabilities",
  "ui_config": {
    "default": "All",
    "placeholder": "Select product type",
    "options": {
      "Smart": "Connected switches/dimmers with WiFi, Bluetooth, or smart home integration (Alexa, Google, etc.)",
      "Non-Smart": "Traditional manual switches and dimmers without connectivity or smart features", 
      "Unknown": "Products where smart capability cannot be determined from the title",
      "N/A": "Products that are not switches or dimmers, or unclear product types"
    }
  }
}
```

**Implementation**: `LabelExpansionStage` class using existing `BaseStage` pattern

### 5.2 Stage 2: Product Assignment

**Purpose**: Assign label values to products based on their titles

**Input**:
- Product titles batch
- Label options from Stage 1
- Original instruction for context

**Expected Output**:
```json
{
  "assignments": {
    "0": "Smart",
    "1": "Non-Smart", 
    "2": "Unknown",
    "3": "N/A"
  }
}
```

**Implementation**: `LabelAssignmentStage` class with batching support

## 6. Service Layer

### 6.1 Main Service Class

```python
class DatabaseProductLabelingService:
    """Orchestrates Template Expansion → Batch Assignment flow using existing tables."""
    
    async def create_label_field(self, request: CreateLabelingRunRequest) -> int:
        """Create label field in project_extend_fields."""
        
    async def execute_labeling(self, field_id: int) -> None:
        """Execute two-stage labeling process."""
        # 1. Template expansion with definitions
        # 2. Batch assignment 
        # 3. Store results in project_extend_data
```

## 7. Configuration

```python
# config.py
PRODUCTS_PER_LABELING_BATCH = 50
MAX_ATTEMPTS_PER_STAGE = 3
LLM_TEMPERATURE = 0.1
LABEL_FIELD_TYPE = "product_label"
```

## 8. Prompt Templates

### 8.1 Template Expansion Prompt

```
# prompts/label_expansion_prompt_v0.txt
You are an expert product categorization specialist. Given a labeling instruction and product category, create a structured labeling scheme with clear definitions for each option.

Instruction: {{instruction}}
Category: {{category}}

Generate a JSON response with:
1. label_name: A concise attribute name (snake_case)
2. label_description: Brief explanation of what this label categorizes
3. ui_config.options: Always include meaningful categories plus "Unknown" and "N/A"
4. Each option value should have a clear definition explaining what products qualify
5. Use "Unknown" for unclear cases, "N/A" for products outside the scope

Required JSON structure:
{
  "label_name": "attribute_name",
  "label_description": "Brief description of what this categorizes",
  "ui_config": {
    "default": "All",
    "placeholder": "Select appropriate placeholder text",
    "options": {
      "Category1": "Clear definition of what products qualify for this category",
      "Category2": "Clear definition of what products qualify for this category",
      "Unknown": "Products where the attribute cannot be determined from the title",
      "N/A": "Products that are outside the scope of this categorization"
    }
  }
}
```

### 8.2 Assignment Prompt

```
# prompts/label_assignment_prompt_v0.txt
You are a product labeling specialist.

**YOUR TASK:** Assign {{label_name}} labels to products based on their titles using the provided label options.

**UNDERSTANDING THE DATA:**
- Product category: {{category}}
- Original instruction: {{instruction}}
- Label description: {{label_description}}
- Each product title should be categorized into the most appropriate label
- Use "Unknown" when the label cannot be determined from the title
- Use "N/A" for products that are outside the scope of this labeling

**AVAILABLE LABEL OPTIONS:**
{{#each options}}
- {{@key}}: {{this}}
{{/each}}

**LABELING GUIDELINES:**
1. **Title Analysis**: Focus on keywords and features mentioned in the product title
2. **Label Definitions**: Match products to labels based on the provided definitions
3. **Clear Assignment**: Each product should fit clearly into one label category
4. **Uncertainty Handling**: Use "Unknown" when the title doesn't provide enough information
5. **Scope Awareness**: Use "N/A" for products that don't belong in this categorization

**REQUIRED OUTPUT FORMAT:**
Return pure JSON mapping each product index to its label value:
{
  "0": "LabelValue1",
  "1": "LabelValue2", 
  "2": "Unknown",
  "3": "N/A",
  ...
}

**CRITICAL RULES:**
- **Complete Coverage**: Every product index from the input must appear exactly once in the output
- **Valid Labels**: Use only the label values provided above (exact case-sensitive matches)
- **Pure JSON**: Return only the JSON object - no explanations or formatting
- **No Duplicates**: Each product index should appear exactly once
- **Accurate Assignment**: Base decisions solely on product title information

**INPUT:**
{{product_list}}
```

## 9. Progress Tracking

Track progress through `product_label_llm_interactions`:
- `total_products`: Set during field creation
- `completed_products`: Updated as batches complete
- `stage`: Current processing stage

## 10. File Storage

Following existing patterns:
```
llm_logs/product_label/
└── FIELD_<field_id>_<ISO>_<hash>/
    ├── prompts/
    │   ├── label_expansion_prompt.txt
    │   └── label_assignment_prompt.txt
    ├── expansion/
    │   └── 20250618T120305Z_expansion_a1_f4c2.json
    └── assignment/
        ├── 20250618T120625Z_b1_a1_9ab1.json
        └── 20250618T120900Z_b2_a1_c1d2.json
```

## 11. Testing Strategy

- **Unit tests**: Model validation, prompt building, response parsing
- **Integration tests**: Database operations with existing tables, file storage
- **LLM tests**: Mock LLM responses, validation logic for definitions
- **End-to-end tests**: Full pipeline execution using real switch/dimmer examples

## 12. Migration Path

1. Create LLM tracking table via migration
2. Implement repositories for existing tables (`project_extend_fields`, `project_extend_data`)
3. Build LLM stages with enhanced prompt templates
4. Implement service layer orchestration
5. Add API endpoint and background task handling
6. Create comprehensive test suite with switch/dimmer examples

## 13. Integration Points

- **Database**: Uses existing `project_extend_fields` and `project_extend_data` tables
- **Products**: References existing `product_wide_table` for product data
- **LLM**: Leverages existing `llm_utils.py` infrastructure
- **Storage**: Uses existing `LLMStorageService` pattern
- **Batching**: Uses existing `make_batches` utility
- **UI**: Label configurations include display-friendly structures for frontend

## 14. Example Use Cases

### Light Switches & Dimmers
- **Smart**: "Kasa Smart Light Switch WiFi", "Lutron Caseta Wireless Dimmer"
- **Non-Smart**: "Leviton Standard Toggle Switch", "Lutron Maestro C.L Dimmer"
- **Unknown**: "Switch Assembly Unit", "Electrical Control Device"
- **N/A**: "Switch Plate Cover", "Wire Nuts"