#!/usr/bin/env python3
"""
Final Aspect Assignment Only Script

This script performs ONLY step 5.4: assign extracted aspects to existing categories.
It uses the existing aspect_category_definitions.json and assigns aspects from 
expanded_review_results.json to these categories.

Usage:
    python final_assign_aspects_only.py

Requirements:
    - expanded_review_results.json (from step 4)
    - aspect_category_definitions.json (existing classification dictionary)
"""

import json
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime
import asyncio

# Import utility modules
from utils.config import get_process_review_config
from utils.llm_utils import initialize_global_llm, safe_llm_call
from utils.prompt_utils import load_prompt
from utils.json_utils import extract_json_from_response
from utils.cache_utils import LLMCache
from utils.rate_limiter import RateLimiter

# === CONFIGURATION ===
config = get_process_review_config()

# Initialize LLM with configuration
llm_manager = initialize_global_llm(
    model_name=config.MODEL_NAME,
    temperature=config.MODEL_TEMPERATURE,
    max_tokens=config.MODEL_MAX_TOKENS
)

# Initialize cache and rate limiter
cache_manager = LLMCache(config.CACHE_DIR)
rate_limiter = RateLimiter(
    max_requests_per_minute=config.MAX_REQUESTS_PER_MINUTE,
    max_input_tokens_per_minute=config.MAX_INPUT_TOKENS_PER_MINUTE,
    max_output_tokens_per_minute=config.MAX_OUTPUT_TOKENS_PER_MINUTE,
    max_concurrent_requests=config.MAX_CONCURRENT_REQUESTS,
    model_max_tokens=config.MODEL_MAX_TOKENS
)

# Load final assignment prompt template
FINAL_ASSIGN_PROMPT_TEMPLATE = load_prompt("final_assign_aspects_prompt_v0.txt", config.PROMPT_DIR)

# Batch size for final assignment
FINAL_ASSIGNMENT_BATCH_SIZE = 150

def extract_aspects_from_review_results(review_results: Dict[str, Any]) -> List[Tuple[str, str, str, str]]:
    """
    Extract all aspects from expanded_review_results.json
    
    Returns:
        List of (aspect_id, aspect_type, category, description) tuples
    """
    all_aspects = []
    
    for asin, data in review_results.items():
        # Extract physical aspects
        if 'phy' in data:
            for physical_category, details in data['phy'].items():
                for pid_detail, sentiments in details.items():
                    pid, detail = pid_detail.split('@', 1) if '@' in pid_detail else (pid_detail, "")
                    formatted_desc = f"{physical_category}: {detail}" if detail else physical_category
                    aspect_id = f"{asin}_{pid}"
                    all_aspects.append((aspect_id, "phy", physical_category, formatted_desc))
        
        # Extract performance aspects  
        if 'perf' in data:
            for perf_category, details in data['perf'].items():
                for perf_id_detail, sentiments in details.items():
                    perf_id, detail = perf_id_detail.split('@', 1) if '@' in perf_id_detail else (perf_id_detail, "")
                    formatted_desc = f"{perf_category}: {detail}" if detail else perf_category
                    aspect_id = f"{asin}_{perf_id}"
                    all_aspects.append((aspect_id, "perf", perf_category, formatted_desc))
        
        # Extract use aspects
        if 'use' in data:
            for use_case, sentiments in data['use'].items():
                formatted_desc = use_case
                aspect_id = f"{asin}_{use_case}"
                all_aspects.append((aspect_id, "use", "use case", formatted_desc))
    
    print(f"提取了 {len(all_aspects)} 个方面问题")
    return all_aspects

def deduplicate_aspects(all_aspects: List[Tuple[str, str, str, str]]) -> Tuple[List[Tuple[str, str]], Dict[str, List[str]], set, Dict[str, int], Dict[str, str]]:
    """
    Remove duplicate aspects and create mapping
    
    Returns:
        - unique_aspects: List of (unified_id, description) for processing
        - aspect_mapping: Map from unified_id to list of original aspect_ids
        - seen_descriptions: Set of normalized descriptions for deduplication
        - aspect_counts: Count of each description for statistics
        - original_to_unified_map: Map from original aspect_id to unified_id
    """
    seen_descriptions = set()
    unique_aspects = []
    aspect_mapping = {}
    aspect_counts = {}
    original_to_unified_map = {}
    
    for aspect_id, aspect_type, category, description in all_aspects:
        # Normalize description for deduplication
        normalized_desc = description.lower().strip()
        
        # Count occurrences
        aspect_counts[normalized_desc] = aspect_counts.get(normalized_desc, 0) + 1
        
        if normalized_desc not in seen_descriptions:
            # This is a new unique description
            seen_descriptions.add(normalized_desc)
            unified_id = f"unified_{len(unique_aspects)}"
            unique_aspects.append((unified_id, description))
            aspect_mapping[unified_id] = [aspect_id]
            original_to_unified_map[aspect_id] = unified_id
        else:
            # This is a duplicate - find the unified_id
            for unified_id, existing_desc in unique_aspects:
                if existing_desc.lower().strip() == normalized_desc:
                    aspect_mapping[unified_id].append(aspect_id)
                    original_to_unified_map[aspect_id] = unified_id
                    break
    
    print(f"去重后剩余 {len(unique_aspects)} 个唯一方面问题")
    print(f"平均每个问题重复 {len(all_aspects) / len(unique_aspects):.1f} 次")
    
    return unique_aspects, aspect_mapping, seen_descriptions, aspect_counts, original_to_unified_map

def format_aspects_for_prompt(aspects: List[Tuple[str, str]]) -> str:
    """Format aspects for the categorization prompt"""
    formatted_lines = []
    for aspect_id, description in aspects:
        formatted_lines.append(f"[{aspect_id}] {description}")
    
    return "\n".join(formatted_lines)

def parse_and_validate_final_categorization_response(response_text: str, expected_ids: set, 
                                                   valid_category_ids: set, aspect_type: str) -> Tuple[bool, Any]:
    """
    Parse and validate the final categorization response
    
    Args:
        response_text: Raw response from LLM
        expected_ids: Set of aspect IDs that should be categorized
        valid_category_ids: Set of valid category IDs
        aspect_type: Type of aspects being categorized
        
    Returns:
        Tuple of (is_valid, parsed_result)
    """
    try:
        # Extract JSON from response
        parsed_result = extract_json_from_response(response_text)
        
        if not isinstance(parsed_result, dict):
            return False, f"Response is not a dictionary: {type(parsed_result)}"
        
        # Validate all expected IDs are present
        response_ids = set(parsed_result.keys())
        missing_ids = expected_ids - response_ids
        extra_ids = response_ids - expected_ids
        
        if missing_ids:
            return False, f"Missing aspect IDs in response: {missing_ids}"
        
        if extra_ids:
            return False, f"Unexpected aspect IDs in response: {extra_ids}"
        
        # Validate all category assignments are valid
        invalid_categories = []
        for aspect_id, category_id in parsed_result.items():
            if category_id not in valid_category_ids:
                invalid_categories.append(f"{aspect_id} -> {category_id}")
        
        if invalid_categories:
            return False, f"Invalid category assignments: {invalid_categories}"
        
        return True, parsed_result
        
    except Exception as e:
        return False, f"Error parsing response: {str(e)}"

async def final_categorize_aspects_batch(aspects: List[Tuple[str, str]], consolidated_categories: Dict[str, Dict[str, Any]],
                                       aspect_type: str, aspect_context: str, product_categories: set, 
                                       max_retries: int = 3) -> Dict[str, str]:
    """
    Perform final categorization of a batch of aspects
    
    Args:
        aspects: List of (aspect_id, description) tuples
        consolidated_categories: Consolidated category definitions
        aspect_type: Type of aspects (phy/perf/use)
        aspect_context: Context description for aspects
        product_categories: Set of product categories
        max_retries: Maximum number of retries
        
    Returns:
        Dictionary mapping aspect_id to category_id
    """
    if not aspects:
        return {}
    
    # Format aspects for prompt
    aspects_text = format_aspects_for_prompt(aspects)
    
    # Format categories for prompt
    categories_text = []
    for cat_id, cat_info in consolidated_categories.items():
        definition = cat_info.get('definition', 'No definition available')
        categories_text.append(f"{cat_id}: {definition}")
    
    categories_formatted = "\n".join(categories_text)
    
    # Prepare prompt
    prompt = FINAL_ASSIGN_PROMPT_TEMPLATE.format(
        aspect_type=aspect_type,
        aspect_context=aspect_context,
        categories_section=categories_formatted,
        formatted_aspects=aspects_text,
        product_context=f"**PRODUCT CONTEXT:** {', '.join(sorted(product_categories))}" if product_categories else ""
    )
    
    expected_ids = {aspect_id for aspect_id, _ in aspects}
    valid_category_ids = set(consolidated_categories.keys())
    
    for attempt in range(max_retries):
        try:
            # Estimate tokens and acquire rate limit permission
            estimated_input_tokens = rate_limiter.estimate_tokens(prompt)
            await rate_limiter.acquire(estimated_input_tokens)
            
            try:
                response = await safe_llm_call(prompt)
                
                # Release rate limiter
                actual_output_tokens = rate_limiter.estimate_tokens(response)
                rate_limiter.release(estimated_input_tokens, actual_output_tokens)
                
            except Exception as e:
                # Always release on error
                rate_limiter.release()
                raise e
            
            if not response or not response.strip():
                print(f"  空响应，重试 {attempt + 1}/{max_retries}")
                continue
            
            # Parse and validate response
            is_valid, result = parse_and_validate_final_categorization_response(
                response, expected_ids, valid_category_ids, aspect_type
            )
            
            if is_valid:
                print(f"  成功分配 {len(result)} 个 {aspect_type} 方面")
                return result
            else:
                print(f"  验证失败 {attempt + 1}/{max_retries}: {result}")
                
        except Exception as e:
            print(f"  错误 {attempt + 1}/{max_retries}: {str(e)}")
    
    print(f"  最终分配失败，返回空结果")
    return {}

async def final_categorize_aspects(aspects: List[Tuple[str, str]], consolidated_categories: Dict[str, Dict[str, Any]],
                                 aspect_type: str, aspect_context: str, product_categories: set, 
                                 max_retries: int = 3) -> Dict[str, str]:
    """
    Perform final categorization of all aspects with batching
    """
    if not aspects:
        print(f"没有 {aspect_type} 方面需要分配")
        return {}
    
    print(f"开始最终分配 {len(aspects)} 个 {aspect_type} 方面到 {len(consolidated_categories)} 个分类")
    
    # Create batches
    batches = []
    for i in range(0, len(aspects), FINAL_ASSIGNMENT_BATCH_SIZE):
        batch = aspects[i:i + FINAL_ASSIGNMENT_BATCH_SIZE]
        batches.append(batch)
    
    print(f"分成 {len(batches)} 个批次处理")
    
    # Process batches
    all_assignments = {}
    for i, batch in enumerate(batches, 1):
        print(f"处理批次 {i}/{len(batches)} ({len(batch)} 个方面)")
        
        batch_assignments = await final_categorize_aspects_batch(
            batch, consolidated_categories, aspect_type, aspect_context, product_categories, max_retries
        )
        
        all_assignments.update(batch_assignments)
    
    print(f"完成 {aspect_type} 方面分配: {len(all_assignments)}/{len(aspects)} 成功")
    return all_assignments

def expand_final_assignments_to_original_aspects(final_assignments: Dict[str, str], 
                                               original_to_unified_map: Dict[str, str],
                                               all_aspects: List[Tuple[str, str, str, str]]) -> Dict[str, str]:
    """
    Expand assignments from unified aspects back to all original aspects
    """
    expanded_assignments = {}
    
    for aspect_id, aspect_type, category, description in all_aspects:
        unified_id = original_to_unified_map.get(aspect_id)
        if unified_id and unified_id in final_assignments:
            expanded_assignments[f"{aspect_id}@{description}"] = final_assignments[unified_id]
    
    return expanded_assignments

def load_product_categories_from_csv() -> set:
    """
    Load product categories from the CSV file's category column
    """
    try:
        products_csv_path = config.get_data_path("result", "product_segment", "combined_products_cleaned", "combined_products_with_final_categories.csv")
        products_df = pd.read_csv(products_csv_path)
        if 'category' in products_df.columns:
            categories = set(products_df['category'].dropna().unique())
            print(f"从CSV加载了 {len(categories)} 个产品分类")
            return categories
        else:
            print(f"Warning: CSV中未找到'category'列")
            return set()
    except FileNotFoundError:
        print(f"未找到产品CSV文件")
        return set()
    except Exception as e:
        print(f"加载产品分类出错: {e}")
        return set()

async def main():
    """
    Main execution function
    """
    print("=== 开始执行第5.4步：最终方面分配 ===")
    
    # Get the latest process review directory
    process_review_dir = config.get_data_path("result", "process_review")
    if not process_review_dir.exists():
        print(f"错误: 未找到process_review目录: {process_review_dir}")
        return
    
    # Find the latest directory (should be from step 4)
    date_dirs = [d for d in process_review_dir.iterdir() if d.is_dir() and d.name.startswith('202')]
    if not date_dirs:
        print(f"错误: 未找到任何日期目录在 {process_review_dir}")
        return
    
    latest_dir = max(date_dirs, key=lambda x: x.name)
    print(f"使用最新的结果目录: {latest_dir}")
    
    # Load expanded review results (from step 4)
    expanded_results_path = latest_dir / "expanded_review_results.json"
    if not expanded_results_path.exists():
        print(f"错误: 未找到expanded_review_results.json在 {expanded_results_path}")
        return
    
    print(f"加载评论结果: {expanded_results_path}")
    with open(expanded_results_path, 'r', encoding='utf-8') as f:
        review_results = json.load(f)
    
    print(f"加载了 {len(review_results)} 个产品的评论数据")
    
    # Load existing aspect category definitions
    aspect_definitions_path = latest_dir / "aspect_category_definitions.json"
    if not aspect_definitions_path.exists():
        print(f"错误: 未找到aspect_category_definitions.json在 {aspect_definitions_path}")
        return
    
    print(f"加载分类定义: {aspect_definitions_path}")
    with open(aspect_definitions_path, 'r', encoding='utf-8') as f:
        aspect_definitions = json.load(f)
    
    # Extract category definitions by type
    category_definitions = aspect_definitions.get('category_definitions', {})
    phy_categories = category_definitions.get('physical_categories', {})
    perf_categories = category_definitions.get('performance_categories', {})
    use_categories = category_definitions.get('use_categories', {})
    
    print(f"加载的分类数量:")
    print(f"  物理分类: {len(phy_categories)}")
    print(f"  性能分类: {len(perf_categories)}")
    print(f"  使用分类: {len(use_categories)}")
    
    # Load product categories
    product_categories = load_product_categories_from_csv()
    
    # Extract all aspects from review results
    print("\n=== 提取所有方面问题 ===")
    all_aspects = extract_aspects_from_review_results(review_results)
    
    # Separate by type
    phy_aspects = [(aid, atype, cat, desc) for aid, atype, cat, desc in all_aspects if atype == 'phy']
    perf_aspects = [(aid, atype, cat, desc) for aid, atype, cat, desc in all_aspects if atype == 'perf']
    use_aspects = [(aid, atype, cat, desc) for aid, atype, cat, desc in all_aspects if atype == 'use']
    
    print(f"按类型分组:")
    print(f"  物理方面: {len(phy_aspects)}")
    print(f"  性能方面: {len(perf_aspects)}")
    print(f"  使用方面: {len(use_aspects)}")
    
    # Process each type
    final_assignments = {}
    
    # Process physical aspects
    if phy_aspects and phy_categories:
        print(f"\n=== 处理物理方面 ===")
        unique_phy, phy_mapping, _, _, phy_unified_map = deduplicate_aspects(phy_aspects)
        
        phy_assignments = await final_categorize_aspects(
            unique_phy, phy_categories, "physical", "physical aspects", product_categories
        )
        
        expanded_phy = expand_final_assignments_to_original_aspects(
            phy_assignments, phy_unified_map, phy_aspects
        )
        final_assignments.update(expanded_phy)
    
    # Process performance aspects
    if perf_aspects and perf_categories:
        print(f"\n=== 处理性能方面 ===")
        unique_perf, perf_mapping, _, _, perf_unified_map = deduplicate_aspects(perf_aspects)
        
        perf_assignments = await final_categorize_aspects(
            unique_perf, perf_categories, "performance", "performance aspects", product_categories
        )
        
        expanded_perf = expand_final_assignments_to_original_aspects(
            perf_assignments, perf_unified_map, perf_aspects
        )
        final_assignments.update(expanded_perf)
    
    # Process use aspects
    if use_aspects and use_categories:
        print(f"\n=== 处理使用方面 ===")
        unique_use, use_mapping, _, _, use_unified_map = deduplicate_aspects(use_aspects)
        
        use_assignments = await final_categorize_aspects(
            unique_use, use_categories, "use", "use case aspects", product_categories
        )
        
        expanded_use = expand_final_assignments_to_original_aspects(
            use_assignments, use_unified_map, use_aspects
        )
        final_assignments.update(expanded_use)
    
    # Save results
    print(f"\n=== 保存结果 ===")
    output_path = latest_dir / "consolidated_aspect_categorization.json"
    
    # Create the final result structure
    result = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_aspects": len(final_assignments),
            "physical_categories": len(phy_categories),
            "performance_categories": len(perf_categories),
            "use_categories": len(use_categories)
        },
        "assignments": final_assignments
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {output_path}")
    print(f"总共分配了 {len(final_assignments)} 个方面问题到分类")
    print("\n=== 第5.4步完成！===")

if __name__ == "__main__":
    asyncio.run(main()) 