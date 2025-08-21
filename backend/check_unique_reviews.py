#!/usr/bin/env python3
"""
Check unique review counts for test ASINs
"""

import asyncio
from core.database.connection import get_supabase_service_client

async def check_unique_reviews():
    client = get_supabase_service_client()
    
    test_asins = ['B0BVKYKKRK', 'B0BVKZLT3B', 'B0BSHKS26L', 'B01EZV35QU', 'B00NG0ELL0', 'B085D8M2MR']
    
    result = client.table('amazon_reviews').select('asin,review_id').in_('asin', test_asins).execute()
    
    asin_counts = {}
    for row in result.data:
        asin = row['asin']
        if asin not in asin_counts:
            asin_counts[asin] = set()
        asin_counts[asin].add(row['review_id'])
    
    print('Unique reviews in amazon_reviews table:')
    for asin in test_asins:
        count = len(asin_counts.get(asin, set()))
        print(f'  {asin}: {count} unique reviews')

if __name__ == "__main__":
    asyncio.run(check_unique_reviews()) 