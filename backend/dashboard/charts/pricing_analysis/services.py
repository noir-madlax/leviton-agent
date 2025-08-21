"""Price Distribution Analysis services for dashboard."""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService
from core.models.filters import ProjectFilters
from dashboard.charts.filters.asin_filter_service import get_filtered_asins
from dashboard.charts.base_service import ChartsBaseService
from .models import (
    PriceDistributionRequest, PriceDistributionResponse, PriceDistributionMetadata,
    PriceVsRevenueRequest, PriceVsRevenueResponse,
    BrandPriceDistributionRequest, BrandPriceDistributionResponse,
    PriceDistributionOverviewRequest, PriceDistributionOverviewResponse, PriceDistributionOverviewData,
    CategoryPriceData, CategoryBrandDistribution, BrandPriceData, PriceStatistics,
    SegmentScatterData, ProductPoint
)

logger = logging.getLogger(__name__)

# ==================== 共享基础服务类 ====================

class BasePricingService:
    """价格分析服务基类 - 包含共享的数据获取和处理方法"""
    
    def __init__(self, supabase_client):
        """初始化服务
        
        Args:
            supabase_client: Supabase客户端实例
        """
        self.supabase = supabase_client
    
    def _get_product_pricing_data(
        self,
        asins: List[str],
        extend_fields: Optional[List[str]] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取产品价格和分类数据，可选携带扩展字段列。

        Args:
            asins: ASIN 列表
            extend_fields: 需要一并返回的扩展字段名称列表（来自 project_extend_data.extend JSONB）。

        Returns:
            包含基础定价/分类字段及可选扩展字段的产品数据列表。
        """
        if not asins:
            return []

        try:
            # 1) 安全拼接 IN 列表
            def _escape_literal(value: str) -> str:
                # 基础转义单引号，避免 SQL 注入；平台 ID 只允许作为字面量使用
                return value.replace("'", "''")

            asin_literals = ", ".join([f"'{_escape_literal(a)}'" for a in asins])

            # 2) 选择列（基础列）
            base_columns = [
                "p.platform_id",
                "p.title",
                "p.brand",
                "p.price_usd",
                "p.unit_price_calculated",
                "p.category",
                "p.past_year_revenue",
                "p.past_year_volume",
                "p.product_url",
            ]

            # 3) 扩展字段列
            join_clause = ""
            extend_selects: List[str] = []

            safe_field_names: List[str] = []
            if extend_fields:
                # 仅允许字母、数字、下划线的字段名，避免 SQL 注入
                import re
                for f in extend_fields:
                    if not isinstance(f, str):
                        continue
                    if re.fullmatch(r"[A-Za-z0-9_]+", f):
                        safe_field_names.append(f)
                    else:
                        logger.warning(f"Skip unsafe extend field name: {f}")

                if safe_field_names:
                    # 如果提供了 project_id，则在 JOIN 条件中加入项目约束
                    if project_id:
                        pid_literal = _escape_literal(str(project_id))
                        join_clause = f"\nLEFT JOIN project_extend_data ped ON ped.asins = p.platform_id AND ped.project_id = '{pid_literal}'"
                    else:
                        join_clause = "\nLEFT JOIN project_extend_data ped ON ped.asins = p.platform_id"
                    for f in safe_field_names:
                        extend_selects.append(f"ped.extend->>'{f}' AS {f}")

            # 4) 组装 SQL（单条语句）
            select_list = ",\n  ".join(base_columns + extend_selects)
            sql = f"""
SELECT
  {select_list}
FROM product_wide_table p
{join_clause}
WHERE p.source = 'amazon'
  AND p.platform_id IN ({asin_literals})
  AND p.price_usd IS NOT NULL
  AND p.unit_price_calculated IS NOT NULL
            """.strip()

            # 打印最终执行的 SQL（用于排查 Unknown/N/A 分组问题）
            try:
                logger.info(f"📝 _get_product_pricing_data SQL = {sql}")
            except Exception:
                pass

            # 5) 通过安全 RPC 执行
            result = self.supabase.rpc('execute_safe_query', {'query_text': sql}).execute()

            if not result or not getattr(result, 'data', None):
                return []

            # 6) 解析 RPC 返回结构 {"result": {col: value, ...}}
            rows: List[Dict[str, Any]] = []
            for row in result.data:
                if 'result' in row and isinstance(row['result'], dict):
                    rows.append(row['result'])
                else:
                    # 兼容可能的平铺返回
                    if isinstance(row, dict):
                        rows.append(row)

            logger.info(f"📊 Retrieved {len(rows)} product records with pricing data (via SQL)")
            return rows
            
        except Exception as e:
            logger.error(f"Error fetching product pricing data with extend fields: {e}", exc_info=True)
            return []

    def _calculate_price_statistics(self, prices: List[float]) -> PriceStatistics:
        """计算价格统计信息"""
        if not prices:
            return PriceStatistics(min=0, q1=0, median=0, mean=0, q3=0, max=0)
        
        prices_array = np.array(prices)
        return PriceStatistics(
            min=float(np.min(prices_array)),
            q1=float(np.percentile(prices_array, 25)),
            median=float(np.median(prices_array)),
            mean=float(np.mean(prices_array)),
            q3=float(np.percentile(prices_array, 75)),
            max=float(np.max(prices_array))
        )
    
    def _generate_metadata(self, filtered_asins_count: int, categories_processed: List[str]) -> PriceDistributionMetadata:
        """生成分析元数据"""
        return PriceDistributionMetadata(
            filtered_asins_count=filtered_asins_count,
            calculation_timestamp=datetime.now().isoformat(),
            timeframe_used="year",
            data_source="product_wide_table",
            categories_processed=categories_processed
        )

# ==================== 价格分布服务 (按产品类型) ====================

class PriceDistributionService(BasePricingService):
    """价格分布分析服务 - 专门用于按产品类型的价格分布图表"""
    
    def get_price_distribution_data(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """获取价格分布数据
        
        Args:
            request: 价格分布请求
            
        Returns:
            PriceDistributionResponse: 价格分布数据
        """
        try:
            logger.info(f"💰 Starting Price Distribution analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取产品价格和分类数据（可选扩展字段）
            extend_field_names: Optional[List[str]] = None
            try:
                if getattr(request, 'filters', None) and getattr(request.filters, 'extend_fields', None):
                    if isinstance(request.filters.extend_fields, dict) and request.filters.extend_fields:
                        seen = set()
                        extend_field_names = [f for f in request.filters.extend_fields.keys() if not (f in seen or seen.add(f))]
            except Exception:
                extend_field_names = None

            products_data = self._get_product_pricing_data(
                filtered_asins,
                extend_fields=extend_field_names,
                project_id=request.project_id,
            )
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 按分类（以及可选扩展字段）分组并计算价格分布
            category_price_data = self._calculate_category_price_distributions(products_data, extend_field_names)
            
            # Step 4: 生成分类名称和颜色
            segment_names = [cat.category for cat in category_price_data]
            segment_colors = self._generate_colors(len(segment_names))
            
            # Step 5: 生成元数据
            metadata = self._generate_metadata(len(filtered_asins), segment_names)
            
            return PriceDistributionResponse(
                priceDistribution=category_price_data,
                segmentNames=segment_names,
                segmentColors=segment_colors,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in PriceDistributionService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _calculate_category_price_distributions(
        self,
        products_data: List[Dict[str, Any]],
        extend_field_names: Optional[List[str]] = None,
    ) -> List[CategoryPriceData]:
        """按分类（以及可选扩展字段）计算价格分布。"""
        # 构建分组键：无扩展字段时仅用 category；有扩展字段时用 category + 扩展字段值组合
        groups = defaultdict(list)

        for product in products_data:
            base_category = product.get('category', 'Unknown') or 'Unknown'
            if not extend_field_names:
                label = base_category
            else:
                values: List[str] = []
                for f in extend_field_names:
                    v = product.get(f)
                    values.append(str(v) if v not in (None, '') else 'Unknown')
                label = f"{base_category} + " + " + ".join(values) if values else base_category

            groups[label].append(product)

        category_price_data: List[CategoryPriceData] = []
        for label, products in groups.items():
            sku_prices = [float(p['price_usd']) for p in products if p.get('price_usd')]
            unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]

            stats = {
                'sku': self._calculate_price_statistics(sku_prices),
                'unit': self._calculate_price_statistics(unit_prices),
            }

            category_data = CategoryPriceData(
                category=label,
                skuPrices=sku_prices,
                unitPrices=unit_prices,
                productCount=len(products),
                stats=stats,
            )
            category_price_data.append(category_data)

        return category_price_data

    def _get_empty_response(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """返回空响应"""
        return PriceDistributionResponse(
            priceDistribution=[],
            segmentNames=[],
            segmentColors=[],
            metadata=self._generate_metadata(0, [])
        )

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色列表"""
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFA07A', '#98D8C8']
        return (base_colors * ((count // len(base_colors)) + 1))[:count]

# ==================== 价格收入散点图服务 ====================

class PriceVsRevenueService(BasePricingService, ChartsBaseService):
    """价格收入散点图分析服务"""
    
    def get_price_vs_revenue_data(self, request: PriceVsRevenueRequest) -> PriceVsRevenueResponse:
        """获取价格收入散点图数据
        
        Args:
            request: 价格收入请求
            
        Returns:
            PriceVsRevenueResponse: 散点图数据
        """
        try:
            logger.info(f"📈 Starting Price vs Revenue analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取产品数据（包含收入信息，基于月度明细聚合），并携带扩展字段
            extend_field_names: Optional[List[str]] = None
            try:
                if getattr(request, 'filters', None) and getattr(request.filters, 'extend_fields', None):
                    if isinstance(request.filters.extend_fields, dict) and request.filters.extend_fields:
                        seen = set()
                        extend_field_names = [f for f in request.filters.extend_fields.keys() if not (f in seen or seen.add(f))]
            except Exception:
                extend_field_names = None

            products_data = self._get_product_pricing_data_with_aggregates(
                filtered_asins,
                request.timeframe,
                extend_fields=extend_field_names,
                project_id=request.project_id,
            )
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 生成分组散点数据（按 category + 扩展字段组合）
            segments_data, segment_labels = self._generate_segment_scatter_data(products_data, extend_field_names)

            # Step 4: 生成元数据
            metadata = self._generate_metadata(len(filtered_asins), segment_labels)

            return PriceVsRevenueResponse(
                segments=segments_data,
                meta=metadata,
            )
            
        except Exception as e:
            logger.error(f"Error in PriceVsRevenueService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _get_product_pricing_data_with_aggregates(self, asins: List[str], timeframe=None, extend_fields: Optional[List[str]] = None, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取产品价格、分类数据，并基于月度明细聚合得到收入与销量。
        
        返回的字段与现有下游一致：
        - platform_id, title, brand, price_usd, unit_price_calculated, category, product_url
        - past_year_revenue: 聚合的 total_revenue
        - past_year_volume: 聚合的 total_units_sold
        """
        try:
            # 1) 聚合月度销售（每个 ASIN 一行）
            aggregates = self.query_monthly_sales_aggregate_with_timeframe(asins, timeframe)
            if not aggregates:
                return []

            # 2) 取 wide 表的基础信息，并可选 JOIN project_extend_data 以读取扩展字段
            extend_selects: List[str] = []
            join_clause = ''
            safe_field_names: List[str] = []
            if extend_fields:
                import re
                for f in extend_fields:
                    if isinstance(f, str) and re.fullmatch(r"[A-Za-z0-9_]+", f):
                        safe_field_names.append(f)
                if safe_field_names:
                    extend_selects = [f"ped.extend->>'{f}' as {f}" for f in safe_field_names]

            # 使用 RPC 以支持自定义 JOIN（保持与 _get_product_pricing_data 的方式一致）
            asin_list = [a.platform_id for a in aggregates]
            # 转义单引号，避免 SQL 注入与语法错误
            def _escape_literal(value: str) -> str:
                return str(value).replace("'", "''")

            asin_literals = ", ".join([f"'{_escape_literal(s)}'" for s in asin_list])

            base_cols = [
                'p.platform_id', 'p.title', 'p.brand', 'p.price_usd', 'p.unit_price_calculated', 'p.category', 'p.product_url'
            ]
            select_list = ",\n  ".join(base_cols + extend_selects)
            if safe_field_names:
                if project_id:
                    pid_literal = str(project_id).replace("'", "''")
                    join_clause = f"\nLEFT JOIN project_extend_data ped ON ped.asins = p.platform_id AND ped.project_id = '{pid_literal}'"
                else:
                    join_clause = "\nLEFT JOIN project_extend_data ped ON ped.asins = p.platform_id"
            sql = f"""
SELECT
  {select_list}
FROM product_wide_table p
{join_clause}
WHERE p.source = 'amazon'
  AND p.platform_id IN ({asin_literals})
""".strip()

            try:
                logger.info(f"📝 _get_product_pricing_data_with_aggregates wide SQL = {sql}")
            except Exception:
                pass

            wide_result = self.supabase.rpc('execute_safe_query', {'query_text': sql}).execute()
            if not wide_result.data:
                return []

            # 3) 合并
            agg_map = {a.platform_id: a for a in aggregates}
            products: List[Dict[str, Any]] = []
            rows: List[Dict[str, Any]] = []
            for r in wide_result.data:
                if 'result' in r and isinstance(r['result'], dict):
                    rows.append(r['result'])
                elif isinstance(r, dict):
                    rows.append(r)

            for row in rows:
                asin = row.get('platform_id')
                agg = agg_map.get(asin)
                if not agg:
                    continue
                price_usd_val = row.get('price_usd')
                unit_price_val = row.get('unit_price_calculated')
                products.append({
                    'platform_id': asin,
                    'title': row.get('title'),
                    'brand': row.get('brand'),
                    'price_usd': float(price_usd_val) if price_usd_val is not None else 0.0,
                    'unit_price_calculated': float(unit_price_val) if unit_price_val is not None else 0.0,
                    'category': row.get('category'),
                    'product_url': row.get('product_url'),
                    'past_year_revenue': float(getattr(agg, 'total_revenue', 0.0) or 0.0),
                    'past_year_volume': int(getattr(agg, 'total_units_sold', 0) or 0),
                    **({f: row.get(f) for f in safe_field_names} if safe_field_names else {}),
                })

            logger.info(f"📊 Retrieved {len(products)} products with aggregated revenue/volume from monthly sales")
            return products
        except Exception as e:
            logger.error(f"Error fetching product data with monthly aggregates: {e}")
            return []

    def _generate_segment_scatter_data(self, products_data: List[Dict[str, Any]], extend_field_names: Optional[List[str]] = None, limit_per_segment: int = 50) -> Tuple[List[SegmentScatterData], List[str]]:
        """按 category + 扩展字段组合生成散点分组数据，并返回分组标签列表。"""
        groups = defaultdict(list)

        for product in products_data:
            base_category = product.get('category', 'Unknown') or 'Unknown'
            if not extend_field_names:
                label = base_category
                extend_map: Dict[str, Any] = {}
            else:
                values: List[str] = []
                extend_map = {}
                for f in extend_field_names:
                    v = product.get(f)
                    extend_map[f] = v if v not in (None, '') else 'Unknown'
                    values.append(str(extend_map[f]))
                label = f"{base_category} + " + " + ".join(values) if values else base_category

            groups[(label, base_category, tuple(sorted(extend_map.items())) if extend_map else tuple())].append(product)

        segments: List[SegmentScatterData] = []
        labels: List[str] = []
        for (label, base_category, extend_items), products in groups.items():
            # 排序并截取点位
            sorted_products = sorted(products, key=lambda x: float(x.get('past_year_revenue', 0)), reverse=True)
            top_products = sorted_products[:limit_per_segment]

            sku_prices = [float(p.get('price_usd', 0)) for p in products if p.get('price_usd') is not None]
            unit_prices = [float(p.get('unit_price_calculated', 0)) for p in products if p.get('unit_price_calculated') is not None]

            price_stats = {
                'sku': self._calculate_price_statistics(sku_prices),
                'unit': self._calculate_price_statistics(unit_prices),
            }

            points: List[ProductPoint] = []
            for p in top_products:
                points.append(ProductPoint(
                    id=p['platform_id'],
                    name=p.get('title', 'Unknown'),
                    brand=p.get('brand', 'Unknown'),
                    price_sku=float(p.get('price_usd', 0) or 0),
                    price_unit=float(p.get('unit_price_calculated', 0) or 0),
                    revenue=float(p.get('past_year_revenue', 0) or 0),
                    volume=float(p.get('past_year_volume', 0) or 0),
                    url=p.get('product_url', ''),
                ))

            segment = SegmentScatterData(
                key=label,
                category=base_category,
                extend_values=dict(extend_items),
                total_products=len(products),
                total_revenue=float(sum(float(x.get('past_year_revenue', 0) or 0) for x in products)),
                total_volume=int(sum(int(x.get('past_year_volume', 0) or 0) for x in products)),
                price_stats=price_stats,
                points=points,
            )
            segments.append(segment)
            labels.append(label)

        # 可按总收入排序分组，便于前端默认展示
        segments.sort(key=lambda s: s.total_revenue, reverse=True)
        labels = [s.key for s in segments]
        return segments, labels

    def _get_empty_response(self, request: PriceVsRevenueRequest) -> PriceVsRevenueResponse:
        """返回空响应"""
        return PriceVsRevenueResponse(
            segments=[],
            meta=self._generate_metadata(0, [])
        )

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色列表"""
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFA07A', '#98D8C8']
        return (base_colors * ((count // len(base_colors)) + 1))[:count]

# ==================== 品牌价格分布服务 ====================

class BrandPriceDistributionService(BasePricingService):
    """品牌价格分布分析服务"""
    
    def get_brand_price_distribution_data(self, request: BrandPriceDistributionRequest) -> BrandPriceDistributionResponse:
        """获取品牌价格分布数据
        
        Args:
            request: 品牌价格分布请求
            
        Returns:
            BrandPriceDistributionResponse: 品牌价格分布数据
        """
        try:
            logger.info(f"🏷️ Starting Brand Price Distribution analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取产品价格和分类数据（可选扩展字段）
            extend_field_names: Optional[List[str]] = None
            try:
                if getattr(request, 'filters', None) and getattr(request.filters, 'extend_fields', None):
                    if isinstance(request.filters.extend_fields, dict) and request.filters.extend_fields:
                        seen = set()
                        extend_field_names = [f for f in request.filters.extend_fields.keys() if not (f in seen or seen.add(f))]
            except Exception:
                extend_field_names = None

            products_data = self._get_product_pricing_data(
                filtered_asins,
                extend_fields=extend_field_names,
                project_id=request.project_id,
            )
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 计算品牌价格分布（按 category + 扩展字段组合）
            brand_price_distributions = self._calculate_brand_price_distributions(products_data, extend_field_names)
            
            # Step 4: 生成分类名称和颜色
            segment_names = [cat.category for cat in brand_price_distributions]
            segment_colors = self._generate_colors(len(segment_names))
            
            # Step 5: 生成元数据
            metadata = self._generate_metadata(len(filtered_asins), segment_names)
            
            return BrandPriceDistributionResponse(
                brandPriceDistribution=brand_price_distributions,
                segmentNames=segment_names,
                segmentColors=segment_colors,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in BrandPriceDistributionService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _calculate_brand_price_distributions(
        self,
        products_data: List[Dict[str, Any]],
        extend_field_names: Optional[List[str]] = None,
    ) -> List[CategoryBrandDistribution]:
        """计算品牌价格分布（支持 category + 扩展字段组合）。"""
        category_groups = defaultdict(lambda: defaultdict(list))

        # 按分类（或组合标签）和品牌分组产品
        for product in products_data:
            base_category = product.get('category', 'Unknown') or 'Unknown'
            brand = product.get('brand', 'Unknown') or 'Unknown'

            if not extend_field_names:
                label = base_category
            else:
                values: List[str] = []
                for f in extend_field_names:
                    v = product.get(f)
                    values.append(str(v) if v not in (None, '') else 'Unknown')
                label = f"{base_category} + " + " + ".join(values) if values else base_category

            category_groups[label][brand].append(product)

        brand_distributions: List[CategoryBrandDistribution] = []
        for label, brand_groups in category_groups.items():
            brands_data: List[BrandPriceData] = []

            for brand, products in brand_groups.items():
                sku_prices = [float(p['price_usd']) for p in products if p.get('price_usd')]
                unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]

                brands_data.append(BrandPriceData(
                    name=brand,
                    skuPrices=sku_prices,
                    unitPrices=unit_prices,
                ))

            brand_distributions.append(CategoryBrandDistribution(
                category=label,
                brands=brands_data,
            ))

        return brand_distributions

    def _get_empty_response(self, request: BrandPriceDistributionRequest) -> BrandPriceDistributionResponse:
        """返回空响应"""
        return BrandPriceDistributionResponse(
            brandPriceDistribution=[],
            segmentNames=[],
            segmentColors=[],
            metadata=self._generate_metadata(0, [])
        )

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色列表"""
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFA07A', '#98D8C8']
        return (base_colors * ((count // len(base_colors)) + 1))[:count]

# ==================== 价格分布概览服务 ====================

class PriceDistributionOverviewService(BasePricingService):
    """价格分布概览服务 - 生成统计表格数据，不使用过滤器"""
    
    def get_overview_data(self, request: PriceDistributionOverviewRequest) -> PriceDistributionOverviewResponse:
        """获取价格分布概览数据
        
        Args:
            request: 价格分布概览请求
            
        Returns:
            PriceDistributionOverviewResponse: 概览表格数据
        """
        try:
            logger.info(f"📊 Starting Price Distribution Overview analysis for project {request.project_id}")
            
            # Step 1: 获取项目的所有ASIN
            all_asins = get_filtered_asins(self.supabase, request)
            
            if not all_asins:
                logger.warning(f"No ASINs found for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(all_asins)} total ASINs for project")
            
            # Step 2: 获取产品价格和分类数据（可选扩展字段）
            extend_field_names: Optional[List[str]] = None
            try:
                # 如果请求里带了扩展字段键，则将键名作为需要返回的列
                if getattr(request, 'filters', None) and getattr(request.filters, 'extend_fields', None):
                    if isinstance(request.filters.extend_fields, dict) and request.filters.extend_fields:
                        extend_field_names = list(request.filters.extend_fields.keys())
                        # 去重并保持顺序
                        seen = set()
                        extend_field_names = [f for f in extend_field_names if not (f in seen or seen.add(f))]
            except Exception:
                extend_field_names = None

            products_data = self._get_product_pricing_data(
                all_asins,
                extend_fields=extend_field_names,
                project_id=request.project_id,
            )
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 按分类（以及可选扩展字段）分组并计算概览统计
            overview_data = self._calculate_overview_statistics(products_data, extend_field_names)
            
            # Step 4: 生成元数据
            segment_names = [item.segment for item in overview_data]
            metadata = self._generate_metadata(len(all_asins), segment_names)
            
            return PriceDistributionOverviewResponse(
                overview_data=overview_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in PriceDistributionOverviewService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _calculate_overview_statistics(self, products_data: List[Dict[str, Any]], extend_field_names: Optional[List[str]] = None) -> List[PriceDistributionOverviewData]:
        """计算概览统计数据，支持 category + 扩展字段组合分组。"""
        # 若未指定扩展字段，保持按分类分组的现有逻辑
        if not extend_field_names:
            category_groups = defaultdict(list)
            for product in products_data:
                category = product.get('category', 'Unknown')
                if category:
                    category_groups[category].append(product)

            overview_data: List[PriceDistributionOverviewData] = []
            for category, products in category_groups.items():
                unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]
                if unit_prices:
                    unit_prices_array = np.array(unit_prices)
                    overview_item = PriceDistributionOverviewData(
                        segment=category,
                        products=len(products),
                        min_price=float(np.min(unit_prices_array)),
                        median_price=float(np.median(unit_prices_array)),
                        max_price=float(np.max(unit_prices_array)),
                        average_price=float(np.mean(unit_prices_array))
                    )
                    overview_data.append(overview_item)

            overview_data.sort(key=lambda x: x.products, reverse=True)
            return overview_data

        # 按 category + 扩展字段值组合进行分组
        combo_groups = defaultdict(list)
        for product in products_data:
            category = product.get('category', 'Unknown') or 'Unknown'
            # 组装扩展字段值序列
            values: List[str] = []
            for field_name in extend_field_names:
                val = product.get(field_name)
                # 将 None/空字符串标准化为 'Unknown'
                values.append(str(val) if val not in (None, '') else 'Unknown')

            # 组合标签：单字段用 "Category + Value"；多字段用 "Category + v1 + v2 + ..."
            if len(values) == 1:
                label = f"{category} + {values[0]}"
            else:
                label = f"{category} + " + " + ".join(values)

            combo_groups[label].append(product)

        overview_data: List[PriceDistributionOverviewData] = []
        for label, products in combo_groups.items():
            unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]
            if unit_prices:
                unit_prices_array = np.array(unit_prices)
                overview_item = PriceDistributionOverviewData(
                    segment=label,
                    products=len(products),
                    min_price=float(np.min(unit_prices_array)),
                    median_price=float(np.median(unit_prices_array)),
                    max_price=float(np.max(unit_prices_array)),
                    average_price=float(np.mean(unit_prices_array))
                )
                overview_data.append(overview_item)
        
        overview_data.sort(key=lambda x: x.products, reverse=True)
        return overview_data

    def _get_empty_response(self, request: PriceDistributionOverviewRequest) -> PriceDistributionOverviewResponse:
        """返回空响应"""
        return PriceDistributionOverviewResponse(
            overview_data=[],
            metadata=self._generate_metadata(0, [])
        )