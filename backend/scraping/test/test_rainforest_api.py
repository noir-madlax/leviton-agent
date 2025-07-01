import os
import json
import requests
from dotenv import load_dotenv

# 加载backend目录下的.env文件
load_dotenv(dotenv_path='backend/.env')

RAINFOREST_API_KEY = os.getenv("RAINFOREST_API_KEY")
RAINFOREST_API_URL = "https://api.rainforestapi.com/request"

def test_category_api():
    """测试Category API的原始返回数据"""
    print("=== Testing Rainforest Category API ===")
    
    if not RAINFOREST_API_KEY:
        print("❌ RAINFOREST_API_KEY not found in environment variables")
        return
    
    # 测试Kitchen Racks & Holders类别 (category_id: 3743971)
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "category",
        "category_id": "3743971",
        "amazon_domain": "amazon.com",
        "page": 1
    }
    
    try:
        print(f"🚀 Calling Rainforest API...")
        print(f"📝 Parameters: {json.dumps(params, indent=2)}")
        
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ API call successful!")
        print(f"📊 Response status: {response.status_code}")
        print(f"💳 Credits used: {data.get('request_info', {}).get('credits_used_this_request', 'N/A')}")
        
        # 分析第一个产品的字段
        category_results = data.get('category_results', [])
        if category_results:
            first_product = category_results[0]
            print(f"\n📦 First product analysis:")
            print(f"   Title: {first_product.get('title', 'N/A')}")
            print(f"   ASIN: {first_product.get('asin', 'N/A')}")
            print(f"   Position: {first_product.get('position', 'N/A')}")
            
            # 检查是否有brand字段
            if 'brand' in first_product:
                print(f"   ✅ Brand field found: {first_product['brand']}")
            else:
                print(f"   ❌ Brand field NOT found")
            
            # 检查recent_sales字段
            if 'recent_sales' in first_product:
                print(f"   ✅ Recent sales field found: {first_product['recent_sales']}")
            else:
                print(f"   ❌ Recent sales field NOT found")
            
            # 列出所有可用字段
            print(f"\n🔍 All available fields in first product:")
            for key in sorted(first_product.keys()):
                value = first_product[key]
                if isinstance(value, (dict, list)):
                    print(f"   {key}: {type(value).__name__} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                else:
                    print(f"   {key}: {value}")
        
        # 保存完整响应到文件以供分析
        output_file = "test_rainforest_category_response.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full response saved to: {output_file}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_product_api():
    """测试Product API的原始返回数据"""
    print("\n=== Testing Rainforest Product API ===")
    
    if not RAINFOREST_API_KEY:
        print("❌ RAINFOREST_API_KEY not found in environment variables")
        return
    
    # 测试一个具体产品 (来自Kitchen Racks & Holders的ASIN)
    asin = "B0BZNPDHR9"  # Vtopmart 4 Pack Bathroom Organizer
    
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "product",
        "asin": asin,
        "amazon_domain": "amazon.com"
    }
    
    try:
        print(f"🚀 Calling Rainforest Product API...")
        print(f"📝 Parameters: {json.dumps(params, indent=2)}")
        
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ API call successful!")
        print(f"📊 Response status: {response.status_code}")
        print(f"💳 Credits used: {data.get('request_info', {}).get('credits_used_this_request', 'N/A')}")
        
        # 分析产品信息
        product = data.get('product', {})
        if product:
            print(f"\n📦 Product analysis:")
            print(f"   Title: {product.get('title', 'N/A')}")
            print(f"   ASIN: {product.get('asin', 'N/A')}")
            
            # 检查是否有brand字段
            if 'brand' in product:
                print(f"   ✅ Brand field found: {product['brand']}")
            else:
                print(f"   ❌ Brand field NOT found")
            
            # 检查feature_bullets中是否有品牌信息
            feature_bullets = product.get('feature_bullets', [])
            print(f"   Feature bullets count: {len(feature_bullets)}")
            
            # 检查specifications
            specifications = product.get('specifications', [])
            print(f"   Specifications count: {len(specifications)}")
            
            # 列出主要字段
            print(f"\n🔍 Main product fields:")
            important_fields = ['title', 'brand', 'asin', 'manufacturer', 'model', 'category', 'categories']
            for field in important_fields:
                if field in product:
                    value = product[field]
                    if isinstance(value, (dict, list)):
                        print(f"   {field}: {type(value).__name__} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                    else:
                        print(f"   {field}: {value}")
                else:
                    print(f"   {field}: NOT FOUND")
        
        # 保存完整响应到文件
        output_file = "test_rainforest_product_response.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full response saved to: {output_file}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def compare_with_existing_data():
    """比较我们现有的数据文件"""
    print("\n=== Comparing with existing scraped data ===")
    
    existing_file = "backend/scraping/data/scraped/amazon/amazon_category_cat_3743971_20250630_193557.json"
    
    try:
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        print(f"📁 Loaded existing file: {existing_file}")
        
        category_results = existing_data.get('category_results', [])
        if category_results:
            first_product = category_results[0]
            
            print(f"\n📦 Existing data analysis:")
            print(f"   Title: {first_product.get('title', 'N/A')}")
            print(f"   ASIN: {first_product.get('asin', 'N/A')}")
            
            # 检查字段
            if 'brand' in first_product:
                print(f"   ✅ Brand field: {first_product['brand']}")
            else:
                print(f"   ❌ Brand field NOT found")
            
            if 'recent_sales' in first_product:
                print(f"   ✅ Recent sales: {first_product['recent_sales']}")
            else:
                print(f"   ❌ Recent sales NOT found")
            
            print(f"\n🔍 All fields in existing data:")
            for key in sorted(first_product.keys()):
                value = first_product[key]
                if isinstance(value, (dict, list)):
                    print(f"   {key}: {type(value).__name__} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                else:
                    print(f"   {key}: {value}")
        
    except FileNotFoundError:
        print(f"❌ Existing file not found: {existing_file}")
    except Exception as e:
        print(f"❌ Error reading existing file: {e}")

if __name__ == "__main__":
    print("🔬 Rainforest API Raw Data Analysis")
    print("=" * 50)
    
    # 测试Category API
    category_data = test_category_api()
    
    # 测试Product API  
    product_data = test_product_api()
    
    # 比较现有数据
    compare_with_existing_data()
    
    print("\n" + "=" * 50)
    print("✅ Analysis complete!")
    print("Check the generated JSON files for detailed API responses.") 