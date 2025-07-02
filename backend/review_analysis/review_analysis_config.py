'''Review Analysis module configuration.'''

# Maximum number of reviews passed to one extraction prompt.
REVIEWS_PER_EXTRACTION_PROMPT: int = 15

# Maximum number of aspects passed to one categorisation prompt.
ASPECTS_PER_CATEGORISATION_PROMPT: int = 40

# Maximum number of categories passed to one consolidation prompt.
CATEGORIES_PER_CONSOLIDATION_PROMPT: int = 30

# Maximum number of aspects in a refinement prompt (placeholder for future stages)
ASPECTS_PER_REFINEMENT_PROMPT: int = 50

# 🚀 NEW: Smart sampling limits for cost control
MAX_REVIEWS_PER_PRODUCT: int = 50  # Max reviews to analyze per product
MAX_TOTAL_REVIEWS_GLOBAL: int = 2000  # Global hard limit across all products
SAMPLE_STRATEGY: str = "mixed"  # "top_rated", "recent", "mixed", "random"

ASPECT_TYPE_MAP: dict[str, tuple[str, str]] = {
    "phy": ("physical", "physical product characteristics"),
    "perf": ("performance", "product performance attributes"),
    "use": ("usability", "product applications and usage scenarios"),
} 