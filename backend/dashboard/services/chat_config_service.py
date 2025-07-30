"""Chat configuration service for handling chart cards and chat messages."""

import logging
from typing import Dict, List, Optional, Any
from supabase import Client
from core.database.connection import get_supabase_client
from dashboard.models import ChatMessage, ChartCardConfig, ChartItemConfig, ChartSectionConfig, ChatConfigResponse

logger = logging.getLogger(__name__)


class ChatConfigService:
    """Service for managing chat configuration data."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.supabase: Client = get_supabase_client()

    def get_chat_config(self) -> ChatConfigResponse:
        """
        Get complete chat configuration for a project.
        Implements priority logic: project-specific config > default config
        """
        try:
            logger.info(f"Fetching chat config for project: {self.project_id}")
            
            # Get chart cards with project priority
            chart_cards = self._get_chart_cards()
            
            # Get chart items grouped by parent card
            chart_items = self._get_chart_items()
            
            # Get chart sections grouped by parent card
            chart_sections = self._get_chart_sections()
            
            # Get chat messages (for future use, currently empty)
            chat_messages = self._get_chat_messages()
            
            # If no configuration found at all, use default config
            if not chart_cards and not chart_items:
                logger.warning(f"No configuration found for project {self.project_id}, using default config")
                return self._get_default_config()
            
            logger.info(f"Chat config fetched successfully: {len(chart_cards)} cards, {sum(len(items) for items in chart_items.values())} items, {sum(len(sections) for sections in chart_sections.values())} sections")
            
            return ChatConfigResponse(
                chat_messages=chat_messages,
                chart_cards=chart_cards,
                chart_items=chart_items,
                chart_sections=chart_sections,
                project_id=self.project_id
            )
            
        except Exception as e:
            logger.error(f"Error fetching chat config for project {self.project_id}: {e}")
            # Return default config as fallback
            return self._get_default_config()

    def _get_chart_cards(self) -> List[ChartCardConfig]:
        """Get chart cards with project priority logic."""
        try:
            # First try to get project-specific config
            result = self.supabase.table('chart_configs').select(
                'card_order, card_id, card_config'
            ).eq('config_type', 'chart_card').eq(
                'project_id', self.project_id
            ).eq('is_active', True).order('card_order').execute()
            
            # If no project-specific config found, use default
            if not result.data:
                logger.info(f"No project-specific chart cards found for {self.project_id}, using default")
                result = self.supabase.table('chart_configs').select(
                    'card_order, card_id, card_config'
                ).eq('config_type', 'chart_card').is_(
                    'project_id', 'null'
                ).eq('is_active', True).order('card_order').execute()
            
            # Convert to ChartCardConfig objects
            chart_cards = []
            for row in result.data:
                chart_cards.append(ChartCardConfig(
                    card_order=row['card_order'],
                    card_id=row['card_id'],
                    card_config=row['card_config']
                ))
            
            logger.info(f"Loaded {len(chart_cards)} chart cards")
            return chart_cards
            
        except Exception as e:
            logger.error(f"Error fetching chart cards: {e}")
            return []

    def _get_chart_items(self) -> Dict[str, List[ChartItemConfig]]:
        """Get chart items grouped by parent card ID with project priority logic."""
        try:
            # First try to get project-specific config
            result = self.supabase.table('chart_configs').select(
                'parent_card_id, chart_order, chart_name, chart_id, chart_component'
            ).eq('config_type', 'chart_item').eq(
                'project_id', self.project_id
            ).eq('is_active', True).order('parent_card_id, chart_order').execute()
            
            # If no project-specific config found, use default
            if not result.data:
                logger.info(f"No project-specific chart items found for {self.project_id}, using default")
                result = self.supabase.table('chart_configs').select(
                    'parent_card_id, chart_order, chart_name, chart_id, chart_component'
                ).eq('config_type', 'chart_item').is_(
                    'project_id', 'null'
                ).eq('is_active', True).order('parent_card_id, chart_order').execute()
            
            # Group by parent card ID
            chart_items: Dict[str, List[ChartItemConfig]] = {}
            for row in result.data:
                parent_card_id = row['parent_card_id']
                if parent_card_id not in chart_items:
                    chart_items[parent_card_id] = []
                
                chart_items[parent_card_id].append(ChartItemConfig(
                    chart_order=row['chart_order'],
                    chart_name=row['chart_name'],
                    chart_id=row['chart_id'],
                    chart_component=row['chart_component']
                ))
            
            total_items = sum(len(items) for items in chart_items.values())
            logger.info(f"Loaded {total_items} chart items for {len(chart_items)} cards")
            return chart_items
            
        except Exception as e:
            logger.error(f"Error fetching chart items: {e}")
            return {}

    def _get_chat_messages(self) -> List[ChatMessage]:
        """Get chat messages with project priority logic."""
        try:
            # First try to get project-specific config
            result = self.supabase.table('chart_configs').select(
                'message_order, message_type, message_content'
            ).eq('config_type', 'chat_message').eq(
                'project_id', self.project_id
            ).eq('is_active', True).order('message_order').execute()
            
            # If no project-specific config found, use default
            if not result.data:
                result = self.supabase.table('chart_configs').select(
                    'message_order, message_type, message_content'
                ).eq('config_type', 'chat_message').is_(
                    'project_id', 'null'
                ).eq('is_active', True).order('message_order').execute()
            
            # Convert to ChatMessage objects
            chat_messages = []
            for row in result.data:
                chat_messages.append(ChatMessage(
                    message_order=row['message_order'],
                    message_type=row['message_type'],
                    message_content=row['message_content']
                ))
            
            logger.info(f"Loaded {len(chat_messages)} chat messages")
            return chat_messages
            
        except Exception as e:
            logger.error(f"Error fetching chat messages: {e}")
            return []

    def _get_chart_sections(self) -> Dict[str, List[ChartSectionConfig]]:
        """Get chart sections grouped by parent card ID with project priority logic.
        Now uses chart_item instead of chart_section for unified configuration."""
        try:
            # First try to get project-specific config
            result = self.supabase.table('chart_configs').select(
                'parent_card_id, chart_order, chart_id, chart_name, is_active'
            ).eq('config_type', 'chart_item').eq(
                'project_id', self.project_id
            ).order('parent_card_id, chart_order').execute()
            
            # If no project-specific config found, use default
            if not result.data:
                logger.info(f"No project-specific chart sections found for {self.project_id}, using default")
                result = self.supabase.table('chart_configs').select(
                    'parent_card_id, chart_order, chart_id, chart_name, is_active'
                ).eq('config_type', 'chart_item').is_(
                    'project_id', 'null'
                ).order('parent_card_id, chart_order').execute()
            
            # Group by parent card ID
            chart_sections: Dict[str, List[ChartSectionConfig]] = {}
            for row in result.data:
                parent_card_id = row['parent_card_id']
                if parent_card_id not in chart_sections:
                    chart_sections[parent_card_id] = []
                
                chart_sections[parent_card_id].append(ChartSectionConfig(
                    chart_order=row['chart_order'],
                    chart_id=row['chart_id'],
                    chart_name=row['chart_name'],
                    is_active=row['is_active']
                ))
            
            logger.info(f"Loaded chart sections for {len(chart_sections)} parent cards")
            return chart_sections
            
        except Exception as e:
            logger.error(f"Error fetching chart sections: {e}")
            return {}

    def _get_default_config(self) -> ChatConfigResponse:
        """Fallback method to return hardcoded default config if database fails."""
        logger.warning("Using fallback default config due to database error")
        
        # Hardcoded fallback config matching the original code
        default_cards = [
            ChartCardConfig(
                card_order=1,
                card_id="brand-analysis",
                card_config={
                    "title": "Market Analysis",
                    "description": "Market share and brand positioning analysis",
                    "icon": "Building",
                    "tabKey": "market-analysis",
                    "aiIntroduction": "Market Analysis"
                }
            ),
            ChartCardConfig(
                card_order=2,
                card_id="pricing-analysis",
                card_config={
                    "title": "Pricing Analysis",
                    "description": "Competitive pricing and distribution analysis",
                    "icon": "Target",
                    "tabKey": "pricing-analysis",
                    "aiIntroduction": "Pricing Analysis"
                }
            ),
            ChartCardConfig(
                card_order=3,
                card_id="review-insights",
                card_config={
                    "title": "Customer Reviews",
                    "description": "Pain points and satisfaction analysis",
                    "icon": "MessageCircle",
                    "tabKey": "review-insights",
                    "aiIntroduction": "Customer Insights"
                }
            ),
            ChartCardConfig(
                card_order=4,
                card_id="competitor-analysis",
                card_config={
                    "title": "Competitive Analysis",
                    "description": "Market positioning and competitive landscape",
                    "icon": "Zap",
                    "tabKey": "competitor-analysis",
                    "aiIntroduction": "Competitive Product Analysis"
                }
            )
        ]
        
        default_items = {
            "brand-analysis": [
                ChartItemConfig(chart_order=1, chart_name="Total addressable market (TAM) and Market Share", chart_id="market-share-analysis"),
                ChartItemConfig(chart_order=2, chart_name="Top 10 Best-Selling Brands", chart_id="brand-analysis"),
                ChartItemConfig(chart_order=3, chart_name="Sales Trend of Top 10 Brands", chart_id="sales-trend-analysis"),
                ChartItemConfig(chart_order=4, chart_name="Top 10 Product Segments by Revenue/Volume", chart_id="market-insights"),
                ChartItemConfig(chart_order=5, chart_name="Market Share by Sales Unit", chart_id="package-preference")
            ],
            "pricing-analysis": [
                ChartItemConfig(chart_order=1, chart_name="Price Distribution Overview", chart_id="price-distribution-overview"),
                ChartItemConfig(chart_order=2, chart_name="Price Distribution by Product Type", chart_id="price-distribution-by-type"),
                ChartItemConfig(chart_order=3, chart_name="Price distribution by Brands", chart_id="price-distribution-by-brands"),
                ChartItemConfig(chart_order=4, chart_name="Price vs. Revenue Distribution of Top Selling 20 Products", chart_id="price-vs-revenue")
            ],
            "review-insights": [
                ChartItemConfig(chart_order=1, chart_name="Top 10 Customer Pain Points", chart_id="customer-pain-points"),
                ChartItemConfig(chart_order=2, chart_name="Top 10 Customer Delights", chart_id="customer-delights"),
                ChartItemConfig(chart_order=3, chart_name="Use Case Sentiment Analysis", chart_id="use-case-sentiment")
            ],
            "competitor-analysis": [
                ChartItemConfig(chart_order=1, chart_name="Customer Satisfaction Overview", chart_id="customer-satisfaction-overview"),
                ChartItemConfig(chart_order=2, chart_name="Product Comparison by Key Dimensions", chart_id="product-comparison-dimensions"),
                ChartItemConfig(chart_order=3, chart_name="Product Comparison by Main Use Cases", chart_id="product-comparison-use-cases")
            ]
        }
        
        # Default chart sections for controlling chart visibility within components
        default_sections = {
            "brand-analysis": [
                ChartSectionConfig(chart_order=1, chart_id="market-share-analysis", chart_name="Market Share Analysis", is_active=True),
                ChartSectionConfig(chart_order=2, chart_id="brand-analysis", chart_name="Sales Trend Analysis", is_active=True),
                ChartSectionConfig(chart_order=3, chart_id="market-insights", chart_name="Market Insights", is_active=True),
                ChartSectionConfig(chart_order=4, chart_id="package-preference", chart_name="Package Preference", is_active=True)
            ],
            "pricing-analysis": [
                ChartSectionConfig(chart_order=1, chart_id="price-distribution-overview", chart_name="Price Distribution Overview", is_active=True),
                ChartSectionConfig(chart_order=2, chart_id="price-vs-revenue", chart_name="Price vs Revenue Analysis", is_active=True),
                ChartSectionConfig(chart_order=3, chart_id="price-distribution-by-type", chart_name="Price Distribution by Type", is_active=True),
                ChartSectionConfig(chart_order=4, chart_id="price-distribution-by-brands", chart_name="Price Distribution by Brands", is_active=True)
            ],
            "competitor-analysis": [
                ChartSectionConfig(chart_order=1, chart_id="customer-satisfaction-overview", chart_name="Customer Satisfaction Overview", is_active=True),
                ChartSectionConfig(chart_order=2, chart_id="product-comparison-dimensions", chart_name="Product Comparison Dimensions", is_active=True),
                ChartSectionConfig(chart_order=3, chart_id="product-comparison-use-cases", chart_name="Product Comparison Use Cases", is_active=True)
            ]
        }
        
        return ChatConfigResponse(
            chat_messages=[],
            chart_cards=default_cards,
            chart_items=default_items,
            chart_sections=default_sections,
            project_id=self.project_id
        ) 