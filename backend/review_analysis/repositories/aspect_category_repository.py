from __future__ import annotations

import logging
from typing import List

from supabase import Client  # type: ignore

logger = logging.getLogger(__name__)

_TABLE = "review_analysis_aspect_categories"


class AspectCategoryRepository:
    """Repository for the aspect_category table."""

    def __init__(self, client: Client):
        self._client = client

    async def batch_insert(self, categories: List[dict]) -> List[int]:
        """Insert categories and return the PK list.
        
        For duplicate categories (same project_id, aspect_type, name, stage),
        returns the existing category PK instead of failing.
        """
        if not categories:
            return []
        
        result_pks = []
        
        for category in categories:
            try:
                # Try to insert the category
                res = self._client.table(_TABLE).insert([category]).execute()
                if res.data:
                    result_pks.append(res.data[0]["category_pk"])
                    logger.debug(f"✅ Inserted new category: {category['name']}")
                else:
                    logger.warning(f"⚠️ Failed to insert category {category['name']}: no data returned")
                    
            except Exception as exc:
                # Check if this is a duplicate key constraint violation
                if hasattr(exc, 'code') and exc.code == '23505':
                    # Duplicate key - fetch the existing category PK
                    try:
                        existing = (
                            self._client.table(_TABLE)
                            .select("category_pk")
                            .eq("project_id", category["project_id"])
                            .eq("aspect_type", category["aspect_type"])
                            .eq("name", category["name"])
                            .eq("stage", category["stage"])
                            .single()
                            .execute()
                        )
                        
                        if existing.data:
                            result_pks.append(existing.data["category_pk"])
                            logger.info(f"🔄 Using existing category: {category['name']} (PK: {existing.data['category_pk']})")
                        else:
                            logger.error(f"❌ Duplicate category {category['name']} but couldn't fetch existing PK")
                            
                    except Exception as fetch_exc:
                        logger.exception(f"❌ Failed to fetch existing category {category['name']}: {fetch_exc}")
                        
                else:
                    # Other types of exceptions - log and continue
                    logger.exception(f"❌ Failed to insert category {category['name']}: {exc}")
        
        logger.info(f"📊 Category insertion summary: {len(result_pks)}/{len(categories)} categories processed")
        return result_pks

    async def get_or_create_category(self, project_id: str, aspect_type: str, name: str, stage: str, definition: str = "") -> int:
        """Get existing category PK or create new one if it doesn't exist."""
        try:
            # Try to get existing category first
            existing = (
                self._client.table(_TABLE)
                .select("category_pk")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_type)
                .eq("name", name)
                .eq("stage", stage)
                .single()
                .execute()
            )
            
            if existing.data:
                logger.debug(f"🔍 Found existing category: {name} (PK: {existing.data['category_pk']})")
                return existing.data["category_pk"]
                
        except Exception:
            # Category doesn't exist, continue to create it
            pass
        
        # Create new category
        try:
            new_category = {
                "project_id": project_id,
                "aspect_type": aspect_type,
                "name": name,
                "stage": stage,
                "definition": definition,
            }
            
            res = self._client.table(_TABLE).insert([new_category]).execute()
            if res.data:
                logger.info(f"✅ Created new category: {name} (PK: {res.data[0]['category_pk']})")
                return res.data[0]["category_pk"]
            else:
                raise RuntimeError(f"Failed to create category {name}: no data returned")
                
        except Exception as exc:
            logger.exception(f"❌ Failed to create category {name}: {exc}")
            raise 