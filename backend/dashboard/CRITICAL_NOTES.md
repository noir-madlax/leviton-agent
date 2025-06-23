# Dashboard API Migration - Critical Notes

## 🎯 Phase 2 Migration Status

### ✅ Completed (5/8 Market Analysis Modules)
- **Brand Analysis API**: Fully migrated to backend with project ASIN filtering
- **Product Analysis API**: Completed with fixed NULL handling
- **Pricing Analysis API**: Completed with fixed NULL handling  
- **Market Insights API**: Completed with fixed NULL handling
- **Package Preference API**: Completed with fixed NULL handling
- **ASIN Extraction Logic**: Fixed to ensure consistent data between preview and saved projects
- **Project Data Isolation**: 100% enforced through `BaseDashboardService`

### 🔄 Remaining Modules (3/8 need migration)
- Review Insights
- Competitor Analysis  
- All Review Data

## 🔑 Core Architecture Principles

### 1. Data Isolation (CRITICAL)
```python
# ALWAYS inherit from BaseDashboardService
class YourService(BaseDashboardService):
    def get_data(self):
        query = self._get_base_product_table().select('...')
        query = self._apply_base_filters(query)
        query = self._apply_asin_filter(query)  # 🔑 MANDATORY
```

### 2. Frontend Logic Replication (CRITICAL)
```python
# MUST match frontend filtering exactly
# Example: revenue filtering
if revenue is None or revenue == 0:
    continue  # Skip items without revenue data
```

### 3. Supabase Query Patterns
```python
# ✅ Correct order
query = (
    self.supabase.table('product_wide_table')
    .select('fields')
    .eq('source', 'amazon')
    .neq('product_segment', 'OUT_OF_SCOPE')
    .not_('estimated_revenue', 'is', None)  # Revenue filter
    .in_('platform_id', asins)  # ASIN filter
)

# ❌ Wrong: Double .select() calls will fail
# ❌ Wrong: Missing ASIN filtering = data leakage
```

## 🚨 CRITICAL LESSON: SQL NULL Handling Error (2024-12-23)

### The Problem
```python
# ❌ This caused 500 API errors across all 4 new services
query = query.neq('estimated_revenue', None)
query = query.neq('price_usd', None)
query = query.neq('product_segment', None)
query = query.neq('pack_count', None)
```

### Error Message
```
{'code': '22P02', 'message': 'invalid input syntax for type numeric: "None"'}
```

### Root Cause
- **Supabase Python client** treats `None` as Python literal string "None"
- **PostgreSQL** expects SQL `NULL`, not Python `None`
- **Different behavior** from JavaScript client where `null` works correctly

### The Fix
```python
# ✅ CORRECT: Filter in Python code, not SQL
for item in result.data:
    revenue = item.get('estimated_revenue')
    if revenue is None or revenue == 0:
        continue  # Skip items without revenue data
```

### Prevention Strategy
1. **Never use `.neq(field, None)` in Supabase Python queries**
2. **Always filter NULL values in Python code after query execution**
3. **Test each service immediately after creation to catch this early**
4. **Follow the BrandAnalysisService pattern that works correctly**

## 🚨 Critical Checks Before Migration

### 1. Frontend Logic Analysis
- [ ] Read original frontend method completely
- [ ] Note ALL filtering conditions (especially NULL value handling)
- [ ] Understand data aggregation logic
- [ ] Check for special business rules

### 2. Data Quality Verification
```sql
-- Always verify data availability first
SELECT COUNT(*) as total,
       COUNT(estimated_revenue) as with_revenue,
       COUNT(monthly_sales_volume) as with_volume
FROM product_wide_table 
WHERE platform_id IN (project_asins);
```

### 3. API Response Format
```python
# MUST return exact same format as frontend
# Use existing TypeScript interfaces as reference
return [
    {
        'brand': brand,
        'dimmerRevenue': revenue,  # Same field names
        'switchRevenue': revenue,
        # ... exact same structure
    }
]
```

## 🛠️ Supabase Python Client Notes

### Query Building
```python
# Correct chaining order
query = (
    supabase.table('table_name')
    .select('columns')
    .eq('field', 'value')
    .neq('field', 'value')
    .not_('field', 'is', None)
    .in_('field', list_values)
)

# Execute once
result = query.execute()
```

### NULL Value Handling
```python
# ✅ CORRECT: Filter NULL values in Python code (safer than SQL)
revenue = item.get('estimated_revenue')
if revenue is None:
    continue  # Skip NULL values

# ❌ WRONG: Avoid SQL NULL filtering with Python None
query = query.neq('estimated_revenue', None)  # Causes PostgreSQL error

# 🚨 CRITICAL LESSON: Supabase Python client's None != SQL NULL
# Always use Python filtering instead of SQL .neq(field, None)
```

## 📋 Migration Checklist Template

For each new service migration:

### Pre-Migration
- [ ] Identify frontend method to replace
- [ ] Read and understand ALL frontend logic
- [ ] Check data availability for test projects
- [ ] Verify filtering conditions

### Implementation  
- [ ] Create service inheriting `BaseDashboardService`
- [ ] Implement `get_data()` method
- [ ] Apply ASIN filtering (`self._apply_asin_filter()`)
- [ ] Match frontend logic exactly
- [ ] Add comprehensive logging

### API Layer
- [ ] Create Pydantic models matching frontend interfaces
- [ ] Add API endpoint with proper error handling
- [ ] Register router in `main.py`

### Frontend Integration
- [ ] Add new method to `DatabaseService`
- [ ] Update main container to use new API
- [ ] Test with projects that have data
- [ ] Verify charts display correctly

### Testing
- [ ] Test with multiple projects
- [ ] Verify data isolation (different projects show different data)
- [ ] Check error handling (projects with no data)
- [ ] Confirm frontend builds successfully

## 🎯 Success Criteria

1. **Data Isolation**: Each project only sees its selected ASINs
2. **Logic Consistency**: Backend returns identical data to original frontend
3. **Error Handling**: Graceful handling of projects with no data
4. **Performance**: No significant performance degradation
5. **Compatibility**: Frontend builds and runs without errors

## 🚫 Common Pitfalls to Avoid

1. **Missing ASIN Filter**: Results in data leakage between projects
2. **SQL NULL Handling**: Use Python filtering instead of complex SQL
3. **Logic Mismatch**: Backend logic differs from frontend causing data inconsistency
4. **Double Query Calls**: Supabase client doesn't support chaining after `.execute()`
5. **Field Name Mismatch**: API response must match TypeScript interfaces exactly

## 📝 Notes

- **ASIN Extraction Logic**: ✅ Fixed in `ProjectService._extract_asins_from_filters()`
- **Data Quality**: Some projects may have no revenue data - this is expected
- **Testing Projects**: Use project ID `e774689a-c232-4445-9b26-1d69191b9762` for testing (has revenue data) 