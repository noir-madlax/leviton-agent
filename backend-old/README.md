# Backend Data Processing Workflow Documentation

This system's goal: Analyze user reviews of switch products on Amazon to identify what users care most about, which products perform well, and which perform poorly.

## Overall Workflow Overview

```
1. Scrape Product Info → 2. Build Product Taxonomy + Assignment → 3. Scrape User Reviews → 4. Extract Structured Review Data → 5. Build Review Taxonomy + Assignment → 6. Analyze Category Feedback → 7. Competitor Analysis → 8. Generate Frontend Data
```

## Core Logic: Build Taxonomy First, Then Assign Raw Data

All categorization steps follow the same pattern:
1. **Read All Raw Data** (product titles or review content)
2. **AI Builds Taxonomy Dictionary** (create standardized categorization system)
3. **Assign Raw Data** (assign each raw item to corresponding category)
4. **Optimize Assignment Results** (adjust assignments as needed)

---

## Detailed Step Descriptions

### Step 1: Scrape Product Information
**Script**: `src/competitor/scrape_best_sellers.py`
**Task**: Scrape basic information of switch products from Amazon and Home Depot
**Input**: Website category lists (e.g., "Dimmer Switches" category)
**Output**:
- `data/scraped/amazon/products/*.json` - Amazon product data
- `data/scraped/home_depot/products/*.json` - Home Depot product data

### Step 2: Product Categorization (4 Sub-steps)
**Script**: `src/competitor/segment_products.py`
**Core Logic**: Build product taxonomy dictionary first, then assign each product to categories

#### Step 2.1: Read All Product Titles
**Input File**: `data/processed/combined_products_cleaned.csv`
**Raw Data Example**:
```csv
title,brand,price_usd
"Leviton SureSlide Dimmer Switch for Dimmable LED, Halogen and Incandescent Bulbs",Leviton,14.07
"Lutron Caseta Smart Dimmer Switch",Lutron,46.95
"GE Toggle Switch Single Pole",GE,3.29
```

#### Step 2.2: AI Builds Product Taxonomy Dictionary
**Prompt File**: `prompt/product_segment/extract_taxonomy_prompt_v0.txt`
**AI Task**: Analyze all product titles, create standardized product categorization system
**AI Output Taxonomy Example**:
```json
{
  "Dimmer Switches": {
    "definition": "Switches that control light brightness, e.g. dimmer controls, brightness adjustment switches",
    "ids": [0, 5, 12]
  },
  "Smart Switches": {
    "definition": "Internet-connected switches with app or voice control, e.g. wifi switches, app-controlled switches", 
    "ids": [1, 8, 15]
  },
  "Toggle Switches": {
    "definition": "Traditional manual on/off switches, e.g. single pole switches, wall toggle switches",
    "ids": [3, 9, 18]
  },
  "OUT_OF_SCOPE": {
    "definition": "Products that clearly don't belong to switches, e.g. outlets, circuit breakers",
    "ids": [7, 11]
  }
}
```

#### Step 2.3: Consolidate Similar Categories
**Prompt File**: `prompt/product_segment/consolidate_taxonomy_prompt_v0.txt`
**AI Task**: Merge similar categories to avoid duplication
**Processing Example**:
```
Input: {"Smart Dimmer Switches": {...}, "Intelligent Dimmer": {...}, "Dimmer Controls": {...}}
Output: {"Smart Dimmer Switches": {...}}  // Consolidated unified category
```

#### Step 2.4: Assign Products to Final Categories
**Prompt File**: `prompt/product_segment/refine_assignments_prompt_v0.txt`
**AI Task**: Assign each product to the most appropriate category
**Assignment Example**:
```
Input Product: "Leviton SureSlide Dimmer Switch for Dimmable LED"
Input Categories: Smart Dimmer Switches, Toggle Switches, Smart Switches
AI Output: Smart Dimmer Switches  // Most appropriate category
```

#### Step 2 Final Output
**File**: `data/result/product_segment/combined_products_cleaned/combined_products_with_final_categories.csv`
**New Field**: `product_segment` - Standardized category for each product
```csv
title,brand,price_usd,product_segment
"Leviton SureSlide Dimmer Switch...",Leviton,14.07,Smart Dimmer Switches
"Lutron Caseta Smart Dimmer Switch",Lutron,46.95,Smart Dimmer Switches  
"GE Toggle Switch Single Pole",GE,3.29,Toggle Switches
```

---

### Step 3: Scrape User Reviews
**Script**: `src/competitor/scrape_reviews.py`
**Task**: Use Apify API to scrape Amazon product reviews
**Input**: Product ASIN list (extracted from Step 2 CSV file)
**Configuration**: Maximum 5 pages of reviews per product, only verified purchase reviews
**Output**: `data/scraped/amazon/review/{ASIN}_*.json` - Review data for each product

---

### Step 4: Structured Review Extraction
**Script**: `src/competitor/process_reviews.py`
**Task**: Convert natural language reviews into structured data, extract user concerns

#### Input Files
1. **Review JSON Files**: `data/scraped/amazon/review/`
2. **Product Category CSV**: `data/result/product_segment/combined_products_cleaned/combined_products_with_final_categories.csv`

**Why Product Category CSV is Needed**:
- Match corresponding product category for each ASIN (from `product_segment` column)
- Provide product context during AI extraction, e.g., "Smart Dimmer Switches" instead of specific product title
- Ensure extracted issues are relevant to product type

#### AI Processing
**Prompt File**: `prompt/extract_review_hierarchy_v0.txt`
**AI Task**: Extract three major types of user concerns from reviews

**Three Category Design Principles** (pre-defined framework):
- **Physical Characteristics (phy)**: Physical attributes of the product, not involving usage
  - Format: `"<PHYSICAL>": {"<PID>@<DETAIL>": {"<SENT>": [ID, ...]}}`
  - Includes: appearance, dimensions, materials, colors, weight, etc.
  - Examples: "metal buttons", "heavy switch", "beautiful color"

- **Performance (perf)**: Product performance and functionality under various conditions
  - Format: `"<PERF>": {"<perf_id>@<DETAIL>": {"<SENT>": {<PERF_REASON>: [ID, ...]}}}`
  - Includes: durability, response speed, stability, compatibility, etc.
  - **PERF_REASON**: References physical aspect IDs (PID) that cause the performance
  - Examples: "switch is responsive", "lasted 2 years", "supports LED lights"

- **Use Cases (use)**: Specific application scenarios and usage methods
  - Format: `"<USE>": {"<SENT>": {<USE_REASON>: [ID, ...]}}`
  - Includes: installation locations, suitable environments, usage methods, etc.
  - **USE_REASON**: References performance IDs (perf_id) or physical IDs (PID) that enable the use case
  - Examples: "suitable for kitchen use", "easy installation", "works with 3-way setup"

**Why These 3 Categories**:
1. **Cover All Product Evaluation Dimensions**: When users evaluate products, they essentially describe what it looks like (physical), how well it works (performance), and what scenarios it fits (usage)
2. **Align with Product Analysis Logic**: This categorization method applies to almost all physical product analysis
3. **Facilitate Subsequent Analysis**: This classification allows AI to establish causal relationships through PERF_REASON and USE_REASON

**Causal Relationship Structure**:
- **Physical → Performance**: PERF_REASON links performance aspects to their physical causes
  - Example: "comfortable button feel (A)" → "easy to operate (a)" where PERF_REASON = "A"
- **Physical/Performance → Use**: USE_REASON links use cases to their enabling factors
  - Example: "easy to operate (a)" → "suitable for elderly users" where USE_REASON = "a"
- **Chain of Causality**: Physical attributes drive performance, which enables specific use cases

#### Processing Example
**Input Review**:
```
"This dimmer switch has a great feel to the buttons and looks very modern. Installation was a bit tricky but works perfectly with LED lights."
```

**AI Structured Output**:
```json
{
  "phy": {
    "Button Interface": {
      "A@comfortable button feel": {"+": [1,3,5]}
    },
    "Visual Appearance": {
      "B@modern appearance": {"+": [1]}
    }
  },
  "perf": {
    "LED Compatibility": {
      "a@supports LED lights": {"+": {"A": [1]}}
    },
    "Overall Performance": {
      "b@works perfectly": {"+": {"A": [1]}}
    }
  },
  "use": {
    "Installation": {
      "+": {"?": [1]}
    },
    "Kitchen Use": {
      "+": {"b": [1]}
    }
  }
}
```

#### Step 4 Output File
**File**: `data/result/process_review/{date}/expanded_review_results.json` (16MB)
**Content**: 500+ products, each containing phy, perf, use structured issues

---

### Step 5: Review Issue Categorization (4 Sub-steps)
**Script**: `src/competitor/categorize_review_aspects.py`
**Core Logic**: Build review taxonomy dictionary first, then assign each issue to categories (same logic as Step 2)

#### Step 5.1: Extract All Issue Points
**Input**: Complex nested JSON from Step 4
**Task**: Extract all user-mentioned issues from complex structure, assign each issue an ID
**Processing Example**:
```
From complex data:
"Button Interface": {"A@comfortable button feel": {"+": [1,3,5]}}

Extract to simple list:
[1] Button Interface: comfortable button feel (from product B0076HPM8A)
[2] Button Interface: button hard to press (from product B002DN8CQ6)  
[3] Visual Appearance: modern appearance (from product B0076HPM8A)
... Total 2000+ issue points extracted
```

#### Step 5.2: AI Builds Review Taxonomy Dictionary
**Prompt File**: `prompt/categorize_review_aspects_prompt_v0.txt`
**AI Task**: Analyze all 2000+ issues, create commercially valuable categorization system

**Key: AI views all issues at once, directly creates complete taxonomy dictionary**

**AI Output Taxonomy Example**:
```json
{
  "Button Interface": {
    "definition": "User interaction experience with physical buttons including tactile feedback, e.g. button feel, pressing force, button layout",
    "ids": [1, 15, 23, 45]
  },
  "Installation": {
    "definition": "Installation process difficulty and compatibility, e.g. installation steps, compatibility issues, required tools",
    "ids": [3, 12, 34, 67]
  },
  "Overall Performance": {
    "definition": "Product overall functional performance and reliability, e.g. operational stability, response speed, durability",
    "ids": [5, 18, 29, 56]
  },
  "Visual Appearance": {
    "definition": "Product visual design and aesthetic effects, e.g. appearance style, color matching, design sense",
    "ids": [7, 22, 41, 88]
  }
}
```

**AI Categorization Intelligence**:
- **Semantic Understanding**: AI knows "comfortable button feel" and "button hard to press" both belong to button interaction issues
- **Business Thinking**: AI creates commercially valuable categories, e.g., "Button Interface" is useful for product teams
- **Naming Standards**: AI uses English naming for subsequent programming processing

#### Step 5.3: Consolidate Similar Categories
**Prompt File**: `prompt/consolidate_aspect_categories_prompt_v0.txt`
**Why Needed**: Due to large data volume, AI processes in batches, different batches may produce similar categories
**Processing Example**:
```
Input multiple batch categories:
Batch A: {"Button Operation Experience": {...}, "Product Appearance Design": {...}}
Batch B: {"Physical Button Interaction": {...}, "Visual Aesthetic Level": {...}}

AI discovers similarities, consolidates output:
{
  "Button Interface": {  // Consolidated "Button Operation Experience" and "Physical Button Interaction"
    "definition": "User interaction experience with physical buttons",
    "merged_from": ["Batch A: Button Operation Experience", "Batch B: Physical Button Interaction"],
    "ids": [1, 15, 23, 45, 67, 89]
  },
  "Visual Appearance": {  // Consolidated "Product Appearance Design" and "Visual Aesthetic Level"  
    "definition": "Product visual design and aesthetic effects",
    "merged_from": ["Batch A: Product Appearance Design", "Batch B: Visual Aesthetic Level"],
    "ids": [7, 22, 41, 88, 92, 103]
  }
}
```

#### Step 5.4: Assign Issues to Final Categories
**Prompt File**: `prompt/final_assign_aspects_prompt_v0.txt`
**AI Task**: Assign each specific issue to the most appropriate category
**Assignment Example**:
```
Input Final Taxonomy Dictionary:
C_0: Button Interface - Button interaction experience
C_1: Visual Appearance - Appearance design aesthetics
C_2: Installation - Installation usage convenience

Input Specific Issues:
[1] comfortable button feel
[2] modern appearance
[3] complex installation

AI Assignment Output:
{
  "1": "C_0",  // button feel → button interaction experience
  "2": "C_1",  // modern appearance → appearance design aesthetics
  "3": "C_2"   // complex installation → installation usage convenience
}
```

#### Step 5 Final Output
1. **`aspect_category_definitions.json` (103KB)** - Final category definitions
```json
{
  "category_definitions": {
    "physical_categories": {
      "Button Interface": {
        "definition": "User interaction experience with physical buttons including tactile feedback, e.g. button feel, pressing force, button layout"
      }
    },
    "performance_categories": {
      "Overall Performance": {
        "definition": "Product overall functional performance and reliability, e.g. operational stability, response speed, durability"
      }
    },
    "use_categories": {
      "Installation": {
        "definition": "Installation process difficulty and compatibility, e.g. installation steps, compatibility issues, required tools"
      }
    }
  }
}
```

2. **`consolidated_aspect_categorization.json` (961KB)** - Issue to category mapping
```json
{
  "B0076HPM8A": {
    "A@comfortable button feel": "Button Interface",
    "B@modern appearance": "Visual Appearance",
    "a@supports LED lights": "Overall Performance"
  }
}
```

---

### Step 6: Analyze Category Feedback
**Script**: `src/competitor/category_feedback_analyzer.py`
**Task**: Calculate user satisfaction for each category, identify pain points
**Input**: Categorization results from Step 5 and review data
**Functions**:
- Calculate positive/negative review ratios for each category
- Identify issues users are most dissatisfied with
- Analyze differences by product type
**Output**: `frontend/lib/categoryFeedback.ts` - Feedback analysis data

### Step 7: Competitor Analysis
**Script**: `src/competitor/competitor_analysis.py`
**Task**: Focus analysis on 6 target competitor products
**Target Products**: Leviton D26HD, D215S, DSL06; Lutron Caseta Diva, Diva; TP Link Switch
**Functions**:
- Generate product vs issue category comparison matrix
- Calculate relative satisfaction rankings
- Identify strengths and weaknesses of each product
**Output**: `frontend/lib/competitorAnalysis.ts` - Competitor comparison data

### Step 8: Generate Frontend Display Data
**Script**: `generate_review_data.py`
**Task**: Prepare detailed review data for frontend interface
**Functions**:
- Extract specific review text for each category
- Support frontend click-to-view details functionality
**Output**: `frontend/lib/reviewData.ts` - Detailed review data

---

## 🎯 From Chaos to Order: System Value

### Pre-processing Chaotic State
```
- Product A: "good button feel", "nice color", "installation trouble"
- Product B: "button hard to press", "modern appearance", "wiring complex"  
- Product C: "easy operation", "simple design", "unclear instructions"
... Each product has different issue descriptions, cannot compare
```

### Post-processing Ordered Results
```json
{
  "standardized_categories": {
    "Button Interface": "Button interaction experience category",
    "Visual Appearance": "Appearance design category", 
    "Installation": "Installation experience category"
  },
  "competitive_analysis": {
    "Product A": {"Button Interface": 4.2, "Visual Appearance": 4.0, "Installation": 2.1},
    "Product B": {"Button Interface": 2.8, "Visual Appearance": 4.5, "Installation": 2.3},
    "Product C": {"Button Interface": 4.0, "Visual Appearance": 4.3, "Installation": 2.0}
  }
}
```

**Clear conclusions can now be drawn**:
- Product A has the best button experience (4.2)
- Product B has the best appearance (4.5)
- All products have poor installation experience (all 2.0-2.3)

---

## Execution Order
1. `scrape_best_sellers.py` (scrape product info)
2. `segment_products.py` (product categorization)  
3. `scrape_reviews.py` (scrape reviews)
4. `process_reviews.py` (review structuring)
5. `categorize_review_aspects.py` (review categorization)
6. `category_feedback_analyzer.py` (analyze feedback)
7. `competitor_analysis.py` (competitor analysis)
8. `generate_review_data.py` (generate frontend data)

## File Structure
```
backend/
├── src/competitor/          # Processing scripts
├── prompt/                  # AI prompts
├── data/                    # Data directory
│   ├── scraped/            # Scraped raw data
│   └── result/             # Processed results
└── frontend/lib/           # Frontend data files
```

## Important Configuration
- Maximum 5 pages of reviews per product
- AI Model: Claude Sonnet 4
- Reviews include verified purchases only
- Target: Detailed analysis of 6 competitor products