#!/usr/bin/env python3
"""
Check the most recent batch_id for test ASIN
"""

import asyncio
from core.database.connection import get_supabase_service_client

async def check_latest_batch():
    client = get_supabase_service_client()
    
    test_asin = 'B0BVKYKKRK'
    
    result = client.table('amazon_products').select('platform_id,batch_id,created_at').eq('platform_id', test_asin).order('created_at', desc=True).limit(1).execute()
    
    print('Most recent product record:')
    for row in result.data:
        print(f'  ASIN: {row["platform_id"]}, Batch: {row["batch_id"]}, Created: {row["created_at"]}')

if __name__ == "__main__":
    asyncio.run(check_latest_batch()) 