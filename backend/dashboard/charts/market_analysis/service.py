"""Market Analysis service for TAM and Market Share calculations."""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict

from dashboard.charts.filters.asin_filter_service import get_filtered_asins
from dashboard.charts.base_models import BaseRequestModel
from dashboard.utils import TimeframeFieldMapper
from .models import (
    TAMMarketShareRequest,
    TAMMarketShareResponse,
    TAMData,
    CategoryMarketShare,
    BrandShareData,
    TAMMarketShareMetadata,
    TopSegmentsByRevenueRequest,
    TopSegmentsByRevenueResponse,
    TopSegmentsByRevenueData,
    TopSegmentsByRevenueMetadata,
    SegmentRevenueData,
    PackageTypeDistributionRequest,
    PackageTypeDistributionResponse,
    PackageTypeDistributionData,
    PackageTypeDistributionMetadata,
    PackageTypeData,
    CategoryPackageDistribution
)

logger = logging.getLogger(__name__)


class TAMMarketShareService:
    """Service for Total Addressable Market and Market Share analysis."""

    def __init__(self, supabase_client):
        """Initialize the service with Supabase client."""
        self.supabase = supabase_client
    
    def get_tam_market_share_data(self, request: TAMMarketShareRequest) -> TAMMarketShareResponse:
        """Get TAM and Market Share data with filtering.
        
        Args:
            request: TAM Market Share request with project_id, filters, and timeframe
            
        Returns:
            TAMMarketShareResponse: Complete TAM and market share analysis
        """
        try:
            logger.info(f"🏢 Starting TAM Market Share analysis for project {request.project_id}")
            
            # Step 1: Use public get_filtered_asins method
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: Get product data from wide table with timeframe support
            product_data = self._get_product_data_from_wide_table(filtered_asins, request.timeframe)
            
            if not product_data:
                logger.warning(f"No product data found for filtered ASINs")
                return self._get_empty_response()
            
            # Step 3: Process data and calculate market shares
            tam_data, category_market_shares = self._calculate_market_shares(product_data)
            
            # Step 4: Generate metadata
            metadata = self._generate_metadata(
                filtered_asins_count=len(filtered_asins),
                product_data=product_data
            )
            
            logger.info(f"✅ TAM Market Share analysis completed successfully")
            
            return TAMMarketShareResponse(
                tam_data=tam_data,
                market_share_by_category=category_market_shares,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error in TAM Market Share analysis: {e}", exc_info=True)
            return self._get_empty_response()

    def _get_product_data_from_wide_table(self, asins: List[str], timeframe=None) -> List[Dict[str, Any]]:
        """Get product data from product_wide_table.
        
        Args:
            asins: List of ASINs to query
            timeframe: Optional TimeframeModel to determine which fields to query
            
        Returns:
            List of product data dictionaries
        """
        try:
            # 使用工具类获取字段名
            revenue_field, volume_field = TimeframeFieldMapper.get_fields(timeframe)
            
            # Build select fields
            select_fields = f'platform_id, brand, category, {revenue_field}, {volume_field}'
            
            logger.info(f"📊 Querying fields: {select_fields}")
            
            # Query product_wide_table for required fields
            query = self.supabase.table('product_wide_table').select(select_fields).in_('platform_id', asins)
            
            result = query.execute()
            
            if not result.data:
                logger.warning("No data found in product_wide_table")
                return []
            
            # Filter out products with missing essential data and normalize field names
            valid_products = []
            for product in result.data:
                if (product.get('brand') and 
                    product.get('category') and 
                    product.get(revenue_field) is not None):
                    
                    # Normalize field names for consistent processing
                    normalized_product = {
                        'platform_id': product.get('platform_id'),
                        'brand': product.get('brand'),
                        'category': product.get('category'),
                        'revenue': product.get(revenue_field, 0),
                        'volume': product.get(volume_field, 0)
                    }
                    valid_products.append(normalized_product)
            
            logger.info(f"📈 Retrieved {len(valid_products)} valid products from wide table using {revenue_field}")
            return valid_products
            
        except Exception as e:
            logger.error(f"Error querying product_wide_table: {e}")
            return []
    
    def _calculate_market_shares(self, product_data: List[Dict[str, Any]]) -> tuple[TAMData, List[CategoryMarketShare]]:
        """Calculate TAM and market shares by category.
        
        Args:
            product_data: List of product data from wide table
            
        Returns:
            Tuple of (TAMData, List[CategoryMarketShare])
        """
        # Group data by category and brand
        category_brand_data = defaultdict(lambda: defaultdict(lambda: {
            'revenue': 0.0,
            'volume': 0,
            'product_count': 0
        }))
        
        total_revenue = 0.0
        total_volume = 0
        total_products = 0
        
        for product in product_data:
            category = product.get('category', 'Unknown')
            brand = product.get('brand', 'Unknown')
            revenue = float(product.get('revenue', 0) or 0)
            volume = int(product.get('volume', 0) or 0)
            
            # Aggregate by category and brand
            category_brand_data[category][brand]['revenue'] += revenue
            category_brand_data[category][brand]['volume'] += volume
            category_brand_data[category][brand]['product_count'] += 1
            
            # Aggregate totals
            total_revenue += revenue
            total_volume += volume
            total_products += 1
        
        # Create TAM data
        tam_data = TAMData(
            total_market_revenue=total_revenue,
            total_market_volume=total_volume,
            total_products=total_products,
            currency="USD"
        )
        
        # Create category market shares
        category_market_shares = []
        
        for category, brand_data in category_brand_data.items():
            # Calculate category totals
            category_revenue = sum(data['revenue'] for data in brand_data.values())
            category_volume = sum(data['volume'] for data in brand_data.values())
            category_products = sum(data['product_count'] for data in brand_data.values())
            
            # Create brand shares for this category
            brand_shares = []
            for rank, (brand, data) in enumerate(
                sorted(brand_data.items(), key=lambda x: x[1]['revenue'], reverse=True), 1
            ):
                market_share_pct = (data['revenue'] / category_revenue * 100) if category_revenue > 0 else 0
                
                brand_shares.append(BrandShareData(
                    brand=brand,
                    revenue=data['revenue'],
                    volume=data['volume'],
                    product_count=data['product_count'],
                    market_share_percentage=round(market_share_pct, 2),
                    rank=rank
                ))
            
            category_market_shares.append(CategoryMarketShare(
                category=category,
                total_revenue=category_revenue,
                total_volume=category_volume,
                total_products=category_products,
                brand_shares=brand_shares
            ))
        
        # Sort categories by revenue (descending)
        category_market_shares.sort(key=lambda x: x.total_revenue, reverse=True)
        
        return tam_data, category_market_shares
    
    def _generate_metadata(self, filtered_asins_count: int, product_data: List[Dict[str, Any]]) -> TAMMarketShareMetadata:
        """Generate metadata for the analysis.
        
        Args:
            filtered_asins_count: Number of ASINs after filtering
            product_data: Product data used in analysis
            
        Returns:
            TAMMarketShareMetadata
        """
        categories = set(p.get('category') for p in product_data if p.get('category'))
        brands = set(p.get('brand') for p in product_data if p.get('brand'))
        
        return TAMMarketShareMetadata(
            filtered_asins_count=filtered_asins_count,
            total_categories=len(categories),
            total_brands=len(brands),
            calculation_timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _get_empty_response(self) -> TAMMarketShareResponse:
        """Return empty response when no data is available."""
        return TAMMarketShareResponse(
            tam_data=TAMData(
                total_market_revenue=0.0,
                total_market_volume=0,
                total_products=0,
                currency="USD"
            ),
            market_share_by_category=[],
            metadata=TAMMarketShareMetadata(
                filtered_asins_count=0,
                total_categories=0,
                total_brands=0,
                calculation_timestamp=datetime.now(timezone.utc).isoformat()
            )
        )


class TopSegmentsByRevenueService:
    """Service for Top 10 Segments by Revenue analysis."""

    def __init__(self, supabase_client):
        """Initialize the service with Supabase client."""
        self.supabase = supabase_client
    
    def get_top_segments_data(self, request: TopSegmentsByRevenueRequest) -> TopSegmentsByRevenueResponse:
        """Get Top Segments data with filtering.
        
        Args:
            request: Top Segments request with project_id, filters, and parameters
            
        Returns:
            TopSegmentsByRevenueResponse: Complete Top Segments analysis
        """
        try:
            logger.info(f"🏆 Starting Top Segments analysis for project {request.project_id}")
            
            # Step 1: Use public get_filtered_asins method
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request.metric_type)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: Get product data from wide table with timeframe support
            product_data = self._get_product_data_from_wide_table(filtered_asins, request.timeframe)
            
            if not product_data:
                logger.warning(f"No product data found for filtered ASINs")
                return self._get_empty_response(request.metric_type)
            
            # Step 3: Get segment assignments
            segment_assignments = self._get_segment_assignments(request.project_id, filtered_asins)
            
            if not segment_assignments:
                logger.warning(f"No segment assignments found for project {request.project_id}")
                return self._get_empty_response(request.metric_type)
            
            # Step 4: Aggregate data by segments
            segment_data = self._aggregate_by_segments(product_data, segment_assignments)
            
            # Step 5: Rank and limit segments
            top_segments = self._rank_and_limit_segments(
                segment_data, 
                request.metric_type, 
                request.limit
            )
            
            # Step 6: Calculate market shares and format response
            segments_with_share = self._calculate_market_shares(top_segments, segment_data)
            response_data = self._format_response_data(segments_with_share, segment_data)
            
            # Step 7: Generate metadata
            metadata = self._generate_metadata(
                filtered_asins_count=len(filtered_asins),
                segment_data=segment_data,
                returned_count=len(segments_with_share),
                metric_type=request.metric_type
            )
            
            logger.info(f"✅ Top Segments analysis completed successfully")
            
            return TopSegmentsByRevenueResponse(
                data=response_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error in Top Segments analysis: {e}", exc_info=True)
            return self._get_empty_response(request.metric_type)

    def _get_product_data_from_wide_table(self, asins: List[str], timeframe=None) -> List[Dict[str, Any]]:
        """Get product data from product_wide_table.
        
        Args:
            asins: List of ASINs to query
            timeframe: Optional TimeframeModel to determine which fields to query
            
        Returns:
            List of product data dictionaries
        """
        try:
            # 使用工具类获取字段名
            revenue_field, volume_field = TimeframeFieldMapper.get_fields(timeframe)
            
            # Build select fields
            select_fields = f'platform_id, brand, category, {revenue_field}, {volume_field}, price_usd'
            
            logger.info(f"📊 Querying fields: {select_fields}")
            
            # Query product_wide_table for required fields
            query = self.supabase.table('product_wide_table').select(select_fields).in_('platform_id', asins)
            result = query.execute()
            
            if not result.data:
                logger.warning("No data found in product_wide_table")
                return []
            
            # Filter out products with missing essential data and normalize field names
            valid_products = []
            for product in result.data:
                if (product.get('brand') and 
                    product.get('category') and 
                    product.get(revenue_field) is not None):
                    
                    # Normalize field names for consistent processing
                    normalized_product = {
                        'platform_id': product.get('platform_id'),
                        'brand': product.get('brand'),
                        'category': product.get('category'),
                        'revenue': float(product.get(revenue_field, 0) or 0),
                        'volume': int(product.get(volume_field, 0) or 0),
                        'price': float(product.get('price_usd', 0) or 0)
                    }
                    valid_products.append(normalized_product)
            
            logger.info(f"📈 Retrieved {len(valid_products)} valid products from wide table using {revenue_field}")
            return valid_products
            
        except Exception as e:
            logger.error(f"Error querying product_wide_table: {e}")
            return []

    def _get_segment_assignments(self, project_id: str, asins: List[str]) -> Dict[str, str]:
        """Get segment assignments mapping.
        
        Args:
            project_id: Project ID
            asins: List of ASINs to get segment assignments for
            
        Returns:
            Dict mapping platform_id to segment_name
        """
        try:
            if not asins:
                return {}
                
            # 查询这些ASINs在product_wide_table中的记录，获取wide_table_id
            wide_table_result = self.supabase.table('product_wide_table')\
                .select('id, platform_id')\
                .in_('platform_id', asins)\
                .execute()
            
            if not wide_table_result.data:
                logger.warning(f"No product_wide_table records found for project ASINs")
                return {}
            
            # 建立platform_id到wide_table_id的映射
            platform_to_wide_id = {item['platform_id']: item['id'] for item in wide_table_result.data}
            wide_table_ids = list(platform_to_wide_id.values())
            
            # 方案1: 直接使用项目ID查询
            assignments_result = self.supabase.table('product_segment_assignments')\
                .select('product_id, segment_name')\
                .eq('project_id', project_id)\
                .in_('product_id', wide_table_ids)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if not assignments_result.data:
                # 方案2: 尝试使用哈希ID方案作为回退
                logger.info(f"No direct segment assignments found, trying hashed project IDs")
                # 这里可以添加哈希ID查询逻辑，暂时简化
                logger.warning(f"No segment assignments found for project {project_id}")
                return {}
            
            # 建立wide_table_id到segment的映射
            wide_id_to_segment = {item['product_id']: item['segment_name'] for item in assignments_result.data}
            
            # 转换为platform_id到segment的映射
            platform_to_segment = {}
            for platform_id, wide_id in platform_to_wide_id.items():
                if wide_id in wide_id_to_segment:
                    platform_to_segment[platform_id] = wide_id_to_segment[wide_id]
            
            logger.info(f"📋 Successfully mapped {len(platform_to_segment)} products to segments")
            return platform_to_segment
                
        except Exception as e:
            logger.error(f"Error getting segment assignments: {e}")
            return {}

    def _aggregate_by_segments(self, products: List[Dict], segment_assignments: Dict[str, str]) -> Dict[str, Dict]:
        """Aggregate data by segments.
        
        Args:
            products: List of product data
            segment_assignments: Dict mapping platform_id to segment_name
            
        Returns:
            Dict with segment aggregated data
        """
        segment_data = defaultdict(lambda: {
            'revenue': 0.0,
            'volume': 0,
            'products': 0,
            'brands': defaultdict(int),
            'total_price': 0.0
        })
        
        for product in products:
            platform_id = product['platform_id']
            segment = segment_assignments.get(platform_id)
            
            if not segment:
                continue  # 跳过没有 segment 分配的产品
            
            segment_data[segment]['revenue'] += product['revenue']
            segment_data[segment]['volume'] += product['volume']
            segment_data[segment]['products'] += 1
            segment_data[segment]['total_price'] += product['price']
            segment_data[segment]['brands'][product['brand']] += 1
        
        return dict(segment_data)

    def _rank_and_limit_segments(self, segment_data: Dict, metric_type: str, limit: int) -> List[Dict]:
        """Rank and limit segment quantity.
        
        Args:
            segment_data: Aggregated segment data
            metric_type: Metric to sort by
            limit: Maximum number of segments to return
            
        Returns:
            List of top segments
        """
        segments = []
        
        for segment_name, data in segment_data.items():
            # 计算平均价格和主要品牌
            avg_price = data['total_price'] / data['products'] if data['products'] > 0 else 0
            top_brand = max(data['brands'].items(), key=lambda x: x[1])[0] if data['brands'] else 'N/A'
            
            segments.append({
                'segment': segment_name,
                'revenue': data['revenue'],
                'volume': data['volume'],
                'products': data['products'],
                'avg_price': avg_price,
                'top_brand': top_brand
            })
        
        # 按指定指标排序
        segments.sort(key=lambda x: x[metric_type], reverse=True)
        
        # 限制数量
        return segments[:limit]

    def _calculate_market_shares(self, top_segments: List[Dict], all_segment_data: Dict) -> List[SegmentRevenueData]:
        """Calculate market shares for top segments.
        
        Args:
            top_segments: List of top segments
            all_segment_data: All segment data for calculating total market
            
        Returns:
            List of SegmentRevenueData with market shares
        """
        total_market_revenue = sum(data['revenue'] for data in all_segment_data.values())
        
        segments_with_share = []
        for rank, segment in enumerate(top_segments, 1):
            market_share = (segment['revenue'] / total_market_revenue * 100) if total_market_revenue > 0 else 0
            
            segments_with_share.append(SegmentRevenueData(
                segment=segment['segment'],
                revenue=segment['revenue'],
                volume=segment['volume'],
                products=segment['products'],
                market_share_percentage=round(market_share, 2),
                rank=rank,
                avg_price=round(segment['avg_price'], 2),
                top_brand=segment['top_brand']
            ))
        
        return segments_with_share

    def _format_response_data(self, segments_with_share: List[SegmentRevenueData], all_segment_data: Dict) -> TopSegmentsByRevenueData:
        """Format the response data.
        
        Args:
            segments_with_share: Segments with calculated market shares
            all_segment_data: All segment data for totals
            
        Returns:
            TopSegmentsByRevenueData
        """
        total_market_revenue = sum(data['revenue'] for data in all_segment_data.values())
        total_market_volume = sum(data['volume'] for data in all_segment_data.values())
        total_products = sum(data['products'] for data in all_segment_data.values())
        
        return TopSegmentsByRevenueData(
            segments=segments_with_share,
            total_market_revenue=total_market_revenue,
            total_market_volume=total_market_volume,
            total_products=total_products,
            currency="USD"
        )

    def _generate_metadata(self, filtered_asins_count: int, segment_data: Dict, returned_count: int, metric_type: str) -> TopSegmentsByRevenueMetadata:
        """Generate metadata for the analysis.
        
        Args:
            filtered_asins_count: Number of ASINs after filtering
            segment_data: All segment data
            returned_count: Number of segments returned
            metric_type: Metric type used for sorting
            
        Returns:
            TopSegmentsByRevenueMetadata
        """
        return TopSegmentsByRevenueMetadata(
            filtered_asins_count=filtered_asins_count,
            total_segments=len(segment_data),
            returned_segments=returned_count,
            metric_type=metric_type,
            calculation_timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _get_empty_response(self, metric_type: str) -> TopSegmentsByRevenueResponse:
        """Return empty response when no data is available."""
        return TopSegmentsByRevenueResponse(
            data=TopSegmentsByRevenueData(
                segments=[],
                total_market_revenue=0.0,
                total_market_volume=0,
                total_products=0,
                currency="USD"
            ),
            metadata=TopSegmentsByRevenueMetadata(
                filtered_asins_count=0,
                total_segments=0,
                returned_segments=0,
                metric_type=metric_type,
                calculation_timestamp=datetime.now(timezone.utc).isoformat()
            )
        )


class PackageTypeDistributionService:
    """Service for Package Type Distribution analysis."""

    def __init__(self, supabase_client):
        """Initialize the service with Supabase client."""
        self.supabase = supabase_client
    
    def get_package_type_distribution_data(
        self, 
        request: PackageTypeDistributionRequest
    ) -> PackageTypeDistributionResponse:
        """Get Package Type Distribution data with filtering.
        
        Args:
            request: Package Type Distribution request with project_id, filters, and parameters
            
        Returns:
            PackageTypeDistributionResponse: Complete Package Type Distribution analysis
        """
        try:
            logger.info(f"📦 Starting Package Type Distribution analysis for project {request.project_id}")
            
            # Step 1: Use public get_filtered_asins method
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request.metric_type, request.timeframe)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: Get package type data from project_extend_data
            package_type_assignments = self._get_package_type_assignments(
                request.project_id, 
                filtered_asins, 
                request.filters
            )
            
            if not package_type_assignments:
                logger.warning(f"No package type data found for project {request.project_id}")
                return self._get_empty_response(request.metric_type, request.timeframe)
            
            # Step 3: Get product data from wide table with timeframe support
            product_data = self._get_product_data_from_wide_table(
                list(package_type_assignments.keys()), 
                request.timeframe
            )
            
            if not product_data:
                logger.warning(f"No product data found for filtered ASINs")
                return self._get_empty_response(request.metric_type, request.timeframe)
            
            # Step 4: Calculate package type distributions
            distribution_data = self._calculate_package_distributions(
                product_data, 
                package_type_assignments, 
                request.metric_type
            )
            
            # Step 5: Generate metadata
            metadata = self._generate_metadata(
                filtered_asins_count=len(filtered_asins),
                distribution_data=distribution_data,
                metric_type=request.metric_type,
                timeframe=request.timeframe
            )
            
            logger.info(f"✅ Package Type Distribution analysis completed successfully")
            
            return PackageTypeDistributionResponse(
                data=distribution_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error in Package Type Distribution analysis: {e}", exc_info=True)
            return self._get_empty_response(request.metric_type, request.timeframe)

    def _get_package_type_assignments(
        self, 
        project_id: str, 
        asins: List[str], 
        filters
    ) -> Dict[str, str]:
        """Get package type assignments mapping.
        
        Args:
            project_id: Project ID
            asins: List of ASINs to get package type assignments for
            filters: Additional filters
            
        Returns:
            Dict mapping platform_id to package_type
        """
        try:
            if not asins:
                return {}
                
            # 从project_extend_data表获取package_type数据
            extend_data_query = self.supabase.table('project_extend_data')\
                .select('asins, extend')\
                .eq('project_id', project_id)\
                .in_('asins', asins)
            
            # 应用extend fields过滤（如果有的话）
            if filters and filters.extend_fields:
                for field_name, field_value in filters.extend_fields.items():
                    if field_value is not None:
                        # 处理布尔值转换
                        if isinstance(field_value, bool):
                            field_value = str(field_value).lower()
                        elif field_value == 'true':
                            field_value = 'true'
                        elif field_value == 'false':
                            field_value = 'false'
                        
                        extend_data_query = extend_data_query.eq(f'extend->>{field_name}', field_value)
                        logger.info(f"Applied extend field filter: {field_name} = {field_value}")
            
            extend_result = extend_data_query.execute()
            
            if not extend_result.data:
                logger.warning(f"No extend data found for project {project_id}")
                return {}
            
            # 提取package_type映射
            package_assignments = {}
            for row in extend_result.data:
                asin = row.get('asins')
                extend = row.get('extend', {})
                package_type = extend.get('package_type')
                
                if package_type and asin:
                    # 将Multiple-X格式统一为Multiple
                    if package_type.startswith('Multiple-'):
                        package_type = 'Multiple'
                    
                    package_assignments[asin] = package_type
            
            logger.info(f"📋 Successfully mapped {len(package_assignments)} products to package types")
            return package_assignments
                
        except Exception as e:
            logger.error(f"Error getting package type assignments: {e}")
            return {}

    def _get_product_data_from_wide_table(self, asins: List[str], timeframe=None) -> List[Dict[str, Any]]:
        """Get product data from product_wide_table.
        
        Args:
            asins: List of ASINs to query
            timeframe: Optional TimeframeModel to determine which fields to query
            
        Returns:
            List of product data dictionaries
        """
        try:
            # 使用工具类获取字段名
            revenue_field, volume_field = TimeframeFieldMapper.get_fields(timeframe)
            
            # Build select fields
            select_fields = f'platform_id, brand, category, {revenue_field}, {volume_field}'
            
            logger.info(f"📊 Querying fields: {select_fields}")
            
            # Query product_wide_table for required fields
            query = self.supabase.table('product_wide_table').select(select_fields).in_('platform_id', asins)
            
            result = query.execute()
            
            if not result.data:
                logger.warning("No data found in product_wide_table")
                return []
            
            # Filter out products with missing essential data and normalize field names
            valid_products = []
            for product in result.data:
                if (product.get('brand') and 
                    product.get('category') and 
                    product.get(revenue_field) is not None):
                    
                    # Normalize field names for consistent processing
                    normalized_product = {
                        'platform_id': product.get('platform_id'),
                        'brand': product.get('brand'),
                        'category': product.get('category'),
                        'revenue': float(product.get(revenue_field, 0) or 0),
                        'volume': int(product.get(volume_field, 0) or 0)
                    }
                    valid_products.append(normalized_product)
            
            logger.info(f"📈 Retrieved {len(valid_products)} valid products from wide table using {revenue_field}")
            return valid_products
            
        except Exception as e:
            logger.error(f"Error querying product_wide_table: {e}")
            return []

    def _calculate_package_distributions(
        self,
        product_data: List[Dict],
        package_assignments: Dict[str, str],
        metric_type: str
    ) -> PackageTypeDistributionData:
        """Calculate package type distributions.
        
        Args:
            product_data: List of product data from wide table
            package_assignments: Dict mapping platform_id to package_type
            metric_type: Metric type for calculations ('revenue' or 'products')
            
        Returns:
            PackageTypeDistributionData
        """
        from collections import defaultdict
        
        # Aggregate data by package type and category
        package_category_data = defaultdict(lambda: defaultdict(lambda: {
            'revenue': 0.0,
            'volume': 0,
            'product_count': 0
        }))
        
        # Overall aggregation
        overall_package_data = defaultdict(lambda: {
            'revenue': 0.0,
            'volume': 0,
            'product_count': 0
        })
        
        total_revenue = 0.0
        total_volume = 0
        total_products = 0
        
        for product in product_data:
            platform_id = product['platform_id']
            package_type = package_assignments.get(platform_id)
            
            if not package_type:
                continue  # Skip products without package type assignment
            
            category = product.get('category', 'Unknown')
            revenue = float(product.get('revenue', 0) or 0)
            volume = int(product.get('volume', 0) or 0)
            
            # Aggregate by package type and category
            package_category_data[category][package_type]['revenue'] += revenue
            package_category_data[category][package_type]['volume'] += volume
            package_category_data[category][package_type]['product_count'] += 1
            
            # Aggregate overall
            overall_package_data[package_type]['revenue'] += revenue
            overall_package_data[package_type]['volume'] += volume
            overall_package_data[package_type]['product_count'] += 1
            
            # Total aggregation
            total_revenue += revenue
            total_volume += volume
            total_products += 1
        
        # Calculate overall distribution
        overall_distribution = self._format_package_type_data(
            overall_package_data, metric_type
        )
        
        # Calculate distribution by category
        distribution_by_category = []
        for category, package_types in package_category_data.items():
            category_total_revenue = sum(data['revenue'] for data in package_types.values())
            category_total_volume = sum(data['volume'] for data in package_types.values())
            category_total_products = sum(data['product_count'] for data in package_types.values())
            
            package_types_formatted = self._format_package_type_data(
                package_types, metric_type
            )
            
            distribution_by_category.append(CategoryPackageDistribution(
                category=category,
                total_revenue=category_total_revenue,
                total_volume=category_total_volume,
                total_products=category_total_products,
                package_types=package_types_formatted
            ))
        
        # Sort categories by total revenue (descending)
        distribution_by_category.sort(key=lambda x: x.total_revenue, reverse=True)
        
        return PackageTypeDistributionData(
            overall_distribution=overall_distribution,
            distribution_by_category=distribution_by_category,
            total_market_revenue=total_revenue,
            total_market_volume=total_volume,
            total_products=total_products,
            metric_type=metric_type,
            currency="USD"
        )

    def _format_package_type_data(
        self, 
        package_data: Dict[str, Dict], 
        metric_type: str
    ) -> List[PackageTypeData]:
        """Format package type data with percentages and ranking.
        
        Args:
            package_data: Dict of package type data
            metric_type: Metric type for calculations
            
        Returns:
            List of formatted PackageTypeData
        """
        if not package_data:
            return []
        
        # Calculate total for percentage calculation
        if metric_type == "products":
            total_metric_value = sum(data['product_count'] for data in package_data.values())
        else:  # revenue
            total_metric_value = sum(data['revenue'] for data in package_data.values())
        
        # Create formatted data
        formatted_data = []
        for package_type, data in package_data.items():
            if metric_type == "products":
                percentage = (data['product_count'] / total_metric_value * 100) if total_metric_value > 0 else 0
            else:  # revenue
                percentage = (data['revenue'] / total_metric_value * 100) if total_metric_value > 0 else 0
            
            formatted_data.append({
                'package_type': package_type,
                'revenue': data['revenue'],
                'volume': data['volume'],
                'product_count': data['product_count'],
                'percentage': round(percentage, 2),
                'sort_value': data['product_count'] if metric_type == "products" else data['revenue']
            })
        
        # Sort by metric type and assign ranks
        formatted_data.sort(key=lambda x: x['sort_value'], reverse=True)
        
        result = []
        for rank, item in enumerate(formatted_data, 1):
            result.append(PackageTypeData(
                package_type=item['package_type'],
                revenue=item['revenue'],
                volume=item['volume'],
                product_count=item['product_count'],
                percentage=item['percentage'],
                rank=rank
            ))
        
        return result

    def _generate_metadata(
        self, 
        filtered_asins_count: int, 
        distribution_data: PackageTypeDistributionData,
        metric_type: str,
        timeframe
    ) -> PackageTypeDistributionMetadata:
        """Generate metadata for the analysis.
        
        Args:
            filtered_asins_count: Number of ASINs after filtering
            distribution_data: Package distribution data
            metric_type: Metric type used
            timeframe: Timeframe used
            
        Returns:
            PackageTypeDistributionMetadata
        """
        timeframe_used = "year"  # default
        if timeframe and timeframe.period:
            timeframe_used = timeframe.period
        
        return PackageTypeDistributionMetadata(
            filtered_asins_count=filtered_asins_count,
            total_categories=len(distribution_data.distribution_by_category),
            total_package_types=len(distribution_data.overall_distribution),
            metric_type=metric_type,
            timeframe_used=timeframe_used,
            calculation_timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _get_empty_response(
        self, 
        metric_type: str, 
        timeframe=None
    ) -> PackageTypeDistributionResponse:
        """Return empty response when no data is available."""
        timeframe_used = "year"  # default
        if timeframe and timeframe.period:
            timeframe_used = timeframe.period
            
        return PackageTypeDistributionResponse(
            data=PackageTypeDistributionData(
                overall_distribution=[],
                distribution_by_category=[],
                total_market_revenue=0.0,
                total_market_volume=0,
                total_products=0,
                metric_type=metric_type,
                currency="USD"
            ),
            metadata=PackageTypeDistributionMetadata(
                filtered_asins_count=0,
                total_categories=0,
                total_package_types=0,
                metric_type=metric_type,
                timeframe_used=timeframe_used,
                calculation_timestamp=datetime.now(timezone.utc).isoformat()
            )
        )
