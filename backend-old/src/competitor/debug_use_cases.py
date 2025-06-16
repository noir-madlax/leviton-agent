#!/usr/bin/env python3

from competitor_analysis import CompetitorAnalyzer

def debug_use_cases():
    data_dir = "/Users/maoc/MIT Dropbox/Chengfeng Mao/JMP/leviton-switch/backend/data/result/process_review/20250609_05"
    analyzer = CompetitorAnalyzer(data_dir)
    analyzer.load_data()
    
    # Debug first product
    product_id = 'B0BVKYKKRK'
    product_data = analyzer.consolidated_data['results'][product_id]
    
    print(f'Product {product_id}:')
    print(f'  In product_mapping: {product_id in analyzer.product_mapping}')
    if product_id in analyzer.product_mapping:
        print(f'  Product name: {analyzer.product_mapping[product_id]["product_name"]}')
    
    print(f'  Has use categorization: {"use" in product_data.get("aspect_categorization", {})}')
    if 'use' in product_data.get('aspect_categorization', {}):
        use_cat = product_data['aspect_categorization']['use']
        print(f'  Use categorization keys: {list(use_cat.keys())[:3]}')
        print(f'  Use categorization values: {list(use_cat.values())[:3]}')
    
    expanded_product = analyzer.expanded_reviews['results'][product_id]
    print(f'  Has expanded use data: {"use" in expanded_product.get("review_analysis", {})}')
    if 'use' in expanded_product.get('review_analysis', {}):
        use_reviews = expanded_product['review_analysis']['use']
        print(f'  Use review keys: {list(use_reviews.keys())[:3]}')
        
        # Check first use case in detail
        first_use_key = list(use_cat.keys())[0]
        final_category = use_cat[first_use_key]
        print(f'\n  Checking use case: {first_use_key} -> {final_category}')
        print(f'  Use case key in reviews: {first_use_key in use_reviews}')
        
        if first_use_key in use_reviews:
            use_case_reviews = use_reviews[first_use_key]
            print(f'  Sentiment keys: {list(use_case_reviews.keys())}')
            
            for sentiment in ['+', '-']:
                if sentiment in use_case_reviews:
                    reviews_list = use_case_reviews[sentiment]
                    print(f'  {sentiment} reviews: {len(reviews_list) if isinstance(reviews_list, list) else "not a list"}')

if __name__ == "__main__":
    debug_use_cases() 