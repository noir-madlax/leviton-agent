#!/usr/bin/env python3
"""
Check products in amazon_products table for test ASIN
"""

import asyncio
from core.database.connection import get_supabase_service_client

async def check_products():
    client = get_supabase_service_client()
    
    test_asin = 'B0BVKYKKRK'
    
    result = client.table('amazon_products').select('platform_id,batch_id,created_at').eq('platform_id', test_asin).execute()
    
    print('Products in amazon_products table:')
    for row in result.data:
        print(f'  ASIN: {row["platform_id"]}, Batch: {row["batch_id"]}, Created: {row["created_at"]}')

if __name__ == "__main__":
    asyncio.run(check_products()) 