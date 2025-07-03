"""Test script for Review Insights migration from old table to new table structure.

This script validates the migration by comparing data from the old product_review_analysis
table with the new table structure (review_analysis_aspects, review_analysis_aspect_categories,
review_analysis_aspect_occurrences).

Usage:
    python test_review_insights_migration.py
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from dashboard.services.review_insights_service import ReviewInsightsService
from core.database.connection import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReviewInsightsMigrationValidator:
    """Validator for Review Insights migration."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.supabase = get_supabase_client()
        
    def get_old_table_stats(self) -> Dict[str, Any]:
        """Get statistics from old table structure."""
        try:
            # Get project ASINs first
            project_result = self.supabase.from_('projects').select('selected_product_asins').eq('id', self.project_id).execute()
            if not project_result.data:
                logger.error(f"Project {self.project_id} not found")
                return {}
            
            project_asins = project_result.data[0]['selected_product_asins'] or []
            if not project_asins:
                logger.warning(f"No ASINs found for project {self.project_id}")
                return {}
            
            # Query old table
            old_query = self.supabase.from_('product_review_analysis').select('''
                product_id,
                aspect_category,
                aspect_subcategory,
                standardized_aspect,
                review_content,
                review_id
            ''').neq('standardized_aspect', 'OUT_OF_SCOPE').in_('product_id', project_asins)
            
            old_result = old_query.execute()
            old_data = old_result.data or []
            
            # Calculate statistics
            categories = {}
            for item in old_data:
                cat = item['aspect_category']
                if cat not in categories:
                    categories[cat] = {
                        'count': 0,
                        'aspects': set(),
                        'products': set(),
                        'reviews': set()
                    }
                categories[cat]['count'] += 1
                categories[cat]['aspects'].add(item['standardized_aspect'])
                categories[cat]['products'].add(item['product_id'])
                categories[cat]['reviews'].add(item['review_id'])
            
            return {
                'total_records': len(old_data),
                'total_categories': len(categories),
                'categories': {k: {
                    'count': v['count'],
                    'unique_aspects': len(v['aspects']),
                    'unique_products': len(v['products']),
                    'unique_reviews': len(v['reviews'])
                } for k, v in categories.items()},
                'project_asins': project_asins,
                'table_source': 'product_review_analysis'
            }
            
        except Exception as e:
            logger.error(f"Error getting old table stats: {e}")
            return {}
    
    def get_new_table_stats(self) -> Dict[str, Any]:
        """Get statistics from new table structure."""
        try:
            # Get project ASINs
            project_result = self.supabase.from_('projects').select('selected_product_asins').eq('id', self.project_id).execute()
            if not project_result.data:
                return {}
            
            project_asins = project_result.data[0]['selected_product_asins'] or []
            if not project_asins:
                return {}
            
            # Query new table structure
            aspects_query = self.supabase.from_('review_analysis_aspects').select('''
                aspect_pk,
                product_id,
                aspect_type,
                detail_text,
                category_pk
            ''').eq('project_id', self.project_id).in_('product_id', project_asins)
            
            aspects_result = aspects_query.execute()
            aspects_data = aspects_result.data or []
            
            # Get categories
            category_pks = list(set([item['category_pk'] for item in aspects_data if item['category_pk']]))
            categories_data = {}
            
            if category_pks:
                categories_query = self.supabase.from_('review_analysis_aspect_categories').select('''
                    category_pk,
                    name,
                    definition,
                    aspect_type
                ''').in_('category_pk', category_pks)
                
                categories_result = categories_query.execute()
                if categories_result.data:
                    categories_data = {item['category_pk']: item for item in categories_result.data}
            
            # Get occurrences with sentiment
            aspect_pks = [item['aspect_pk'] for item in aspects_data]
            sentiment_stats = {}
            
            if aspect_pks:
                batch_size = 100
                for i in range(0, len(aspect_pks), batch_size):
                    batch_pks = aspect_pks[i:i + batch_size]
                    occurrences_query = self.supabase.from_('review_analysis_aspect_occurrences').select('''
                        aspect_pk,
                        sentiment,
                        review_id
                    ''').in_('aspect_pk', batch_pks)
                    
                    occurrences_result = occurrences_query.execute()
                    if occurrences_result.data:
                        for occ in occurrences_result.data:
                            aspect_pk = occ['aspect_pk']
                            if aspect_pk not in sentiment_stats:
                                sentiment_stats[aspect_pk] = {'positive': 0, 'negative': 0, 'neutral': 0, 'reviews': set()}
                            
                            sentiment = occ['sentiment']
                            if sentiment == '+':
                                sentiment_stats[aspect_pk]['positive'] += 1
                            elif sentiment == '-':
                                sentiment_stats[aspect_pk]['negative'] += 1
                            else:
                                sentiment_stats[aspect_pk]['neutral'] += 1
                            sentiment_stats[aspect_pk]['reviews'].add(occ['review_id'])
            
            # Calculate statistics by type
            type_stats = {}
            for aspect in aspects_data:
                aspect_type = aspect['aspect_type']
                if aspect_type not in type_stats:
                    type_stats[aspect_type] = {
                        'count': 0,
                        'categories': set(),
                        'products': set(),
                        'total_occurrences': 0,
                        'positive_occurrences': 0,
                        'negative_occurrences': 0,
                        'reviews': set()
                    }
                
                type_stats[aspect_type]['count'] += 1
                type_stats[aspect_type]['products'].add(aspect['product_id'])
                
                category_pk = aspect['category_pk']
                if category_pk in categories_data:
                    type_stats[aspect_type]['categories'].add(categories_data[category_pk]['name'])
                
                aspect_pk = aspect['aspect_pk']
                if aspect_pk in sentiment_stats:
                    stats = sentiment_stats[aspect_pk]
                    type_stats[aspect_type]['total_occurrences'] += sum([stats['positive'], stats['negative'], stats['neutral']])
                    type_stats[aspect_type]['positive_occurrences'] += stats['positive']
                    type_stats[aspect_type]['negative_occurrences'] += stats['negative']
                    type_stats[aspect_type]['reviews'].update(stats['reviews'])
            
            return {
                'total_aspects': len(aspects_data),
                'total_categories': len(categories_data),
                'total_occurrences': sum([sum([s['positive'], s['negative'], s['neutral']]) for s in sentiment_stats.values()]),
                'type_stats': {k: {
                    'aspect_count': v['count'],
                    'unique_categories': len(v['categories']),
                    'unique_products': len(v['products']),
                    'total_occurrences': v['total_occurrences'],
                    'positive_occurrences': v['positive_occurrences'],
                    'negative_occurrences': v['negative_occurrences'],
                    'unique_reviews': len(v['reviews']),
                    'sentiment_breakdown': {
                        'positive_rate': round((v['positive_occurrences'] / max(1, v['total_occurrences'])) * 100, 2),
                        'negative_rate': round((v['negative_occurrences'] / max(1, v['total_occurrences'])) * 100, 2)
                    }
                } for k, v in type_stats.items()},
                'project_asins': project_asins,
                'table_source': 'new_table_structure'
            }
            
        except Exception as e:
            logger.error(f"Error getting new table stats: {e}")
            return {}
    
    def test_new_api_service(self) -> Dict[str, Any]:
        """Test the new Review Insights API service."""
        try:
            service = ReviewInsightsService(project_id=self.project_id)
            result = service.get_data()
            
            return {
                'success': True,
                'pain_points_count': len(result.get('painPoints', [])),
                'customer_likes_count': len(result.get('customerLikes', [])),
                'underserved_use_cases_count': len(result.get('underservedUseCases', [])),
                'pain_points_sample': result.get('painPoints', [])[:3],
                'customer_likes_sample': result.get('customerLikes', [])[:3],
                'underserved_use_cases_sample': result.get('underservedUseCases', [])[:3],
                'api_source': 'new_review_insights_service'
            }
            
        except Exception as e:
            logger.error(f"Error testing new API service: {e}")
            return {
                'success': False,
                'error': str(e),
                'api_source': 'new_review_insights_service'
            }
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate comprehensive migration validation report."""
        logger.info(f"🔍 Starting migration validation for project {self.project_id}")
        
        # Collect all data
        old_stats = self.get_old_table_stats()
        new_stats = self.get_new_table_stats()
        api_test = self.test_new_api_service()
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_id': self.project_id,
            'migration_status': 'unknown',
            'old_table_stats': old_stats,
            'new_table_stats': new_stats,
            'api_test_results': api_test,
            'comparison': {},
            'recommendations': []
        }
        
        # Compare data
        if old_stats and new_stats:
            report['comparison'] = {
                'data_volume_comparison': {
                    'old_records': old_stats.get('total_records', 0),
                    'new_aspects': new_stats.get('total_aspects', 0),
                    'new_occurrences': new_stats.get('total_occurrences', 0),
                    'volume_ratio': round(new_stats.get('total_occurrences', 0) / max(1, old_stats.get('total_records', 1)), 2)
                },
                'category_mapping': {
                    'old_categories': list(old_stats.get('categories', {}).keys()),
                    'new_types': list(new_stats.get('type_stats', {}).keys()),
                    'sentiment_analysis_available': new_stats.get('total_occurrences', 0) > 0
                }
            }
            
            # Determine migration status
            if (new_stats.get('total_aspects', 0) > 0 and 
                new_stats.get('total_occurrences', 0) > 0 and
                api_test.get('success', False)):
                report['migration_status'] = 'ready'
                report['recommendations'].append("✅ Migration data available and API working correctly")
            else:
                report['migration_status'] = 'incomplete'
                report['recommendations'].append("⚠️ Migration data incomplete or API issues detected")
        
        # API specific recommendations
        if api_test.get('success', False):
            report['recommendations'].append(f"✅ New API returned {api_test.get('pain_points_count', 0)} pain points, {api_test.get('customer_likes_count', 0)} customer likes")
        else:
            report['recommendations'].append(f"❌ API test failed: {api_test.get('error', 'Unknown error')}")
        
        return report


def main():
    """Main function to run migration validation."""
    # Test with specified project ID
    project_id = "c6105ab7-e69c-4fd9-8bbd-8a1254cd5c74"
    
    logger.info(f"🚀 Starting Review Insights Migration Validation")
    logger.info(f"📊 Testing with project: {project_id}")
    
    validator = ReviewInsightsMigrationValidator(project_id)
    report = validator.generate_migration_report()
    
    # Print report
    print("\n" + "="*80)
    print("📋 REVIEW INSIGHTS MIGRATION VALIDATION REPORT")
    print("="*80)
    print(f"⏰ Timestamp: {report['timestamp']}")
    print(f"🆔 Project ID: {report['project_id']}")
    print(f"📊 Migration Status: {report['migration_status'].upper()}")
    print()
    
    # Old table stats
    old_stats = report.get('old_table_stats', {})
    print("📚 OLD TABLE STRUCTURE (product_review_analysis):")
    print(f"  - Total Records: {old_stats.get('total_records', 0)}")
    print(f"  - Categories: {old_stats.get('total_categories', 0)}")
    for cat, stats in old_stats.get('categories', {}).items():
        print(f"    • {cat}: {stats['count']} records, {stats['unique_aspects']} aspects")
    print()
    
    # New table stats
    new_stats = report.get('new_table_stats', {})
    print("🆕 NEW TABLE STRUCTURE:")
    print(f"  - Total Aspects: {new_stats.get('total_aspects', 0)}")
    print(f"  - Total Occurrences: {new_stats.get('total_occurrences', 0)}")
    print(f"  - Categories: {new_stats.get('total_categories', 0)}")
    for type_name, stats in new_stats.get('type_stats', {}).items():
        print(f"    • {type_name}: {stats['aspect_count']} aspects, {stats['total_occurrences']} occurrences")
        print(f"      Sentiment: {stats['sentiment_breakdown']['positive_rate']}% positive, {stats['sentiment_breakdown']['negative_rate']}% negative")
    print()
    
    # API test results
    api_test = report.get('api_test_results', {})
    print("🔧 API TEST RESULTS:")
    if api_test.get('success', False):
        print(f"  ✅ Status: SUCCESS")
        print(f"  - Pain Points: {api_test.get('pain_points_count', 0)}")
        print(f"  - Customer Likes: {api_test.get('customer_likes_count', 0)}")
        print(f"  - Underserved Use Cases: {api_test.get('underserved_use_cases_count', 0)}")
    else:
        print(f"  ❌ Status: FAILED")
        print(f"  - Error: {api_test.get('error', 'Unknown')}")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS:")
    for rec in report.get('recommendations', []):
        print(f"  {rec}")
    print()
    
    # Save detailed report
    filename = f"migration_report_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: {filename}")
    print("="*80)


if __name__ == "__main__":
    main() 