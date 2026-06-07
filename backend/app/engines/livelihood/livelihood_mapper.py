from typing import Dict, Any

# Predefined Archetype Schemas
ARCHETYPES = {
    0: {
        "label": "General Micro-Enterprise",
        "description": "Unclassified or general small-scale business activity.",
        "cluster_id": 0
    },
    1: {
        "label": "Trade & Retail",
        "description": "Buying and selling of goods, including kirana stores, apparel, and hardware.",
        "cluster_id": 1
    },
    2: {
        "label": "Services",
        "description": "Service-oriented activities including tailoring, salons, repairs, and professional services.",
        "cluster_id": 2
    },
    3: {
        "label": "Agri-Allied",
        "description": "Farming, dairy, poultry, and agriculture-adjacent operations.",
        "cluster_id": 3
    },
    4: {
        "label": "Manufacturing",
        "description": "Small scale production, handicrafts, and assembly.",
        "cluster_id": 4
    },
    5: {
        "label": "Transport & Logistics",
        "description": "Transportation, delivery, auto-rickshaw, and logistics operations.",
        "cluster_id": 5
    }
}

# Exhaustive O(1) Lookup Dictionary
LIVELIHOOD_DICTIONARY = {
    # Trade & Retail
    "kirana": 1, "grocery": 1, "apparel": 1, "clothing": 1, "hardware": 1,
    "retail": 1, "shop": 1, "store": 1, "medical store": 1, "pharmacy": 1,
    "stationery": 1, "footwear": 1, "electronics": 1, "mobile shop": 1,
    "general store": 1, "wholesale": 1, "trade": 1, "vendor": 1, "vegetable vendor": 1,
    
    # Services
    "tailoring": 2, "salon": 2, "beauty parlor": 2, "barber": 2, "repair": 2,
    "mechanic": 2, "electrician": 2, "plumber": 2, "carpenter": 2, "laundry": 2,
    "dry cleaning": 2, "tuition": 2, "coaching": 2, "catering": 2, "food stall": 2,
    "restaurant": 2, "cafe": 2, "hotel": 2, "photography": 2, "clinic": 2,
    "services": 2, "consultancy": 2, "it services": 2, "cyber cafe": 2,
    
    # Agri-Allied
    "dairy": 3, "poultry": 3, "farming": 3, "agriculture": 3, "livestock": 3,
    "fishery": 3, "animal husbandry": 3, "nursery": 3, "horticulture": 3,
    "floriculture": 3, "agri-allied": 3, "tractor services": 3,
    
    # Manufacturing
    "manufacturing": 4, "handicrafts": 4, "pottery": 4, "weaving": 4, 
    "textile": 4, "food processing": 4, "baking": 4, "bakery": 4, 
    "furniture making": 4, "leather work": 4, "metal work": 4, "factory": 4,
    "production": 4, "stitching": 4, "embroidery": 4,
    
    # Transport & Logistics
    "transport": 5, "logistics": 5, "auto rickshaw": 5, "taxi": 5, "cab service": 5,
    "delivery": 5, "trucking": 5, "freight": 5, "driver": 5, "courier": 5,
    "movers": 5, "goods carrier": 5, "e-rickshaw": 5
}

def map_livelihood(primary_business: str) -> Dict[str, Any]:
    """
    Deterministically maps a primary_business string to a livelihood archetype.
    
    Signature constraints:
    Accepts ONLY a string. The applicant dictionary must never be passed here,
    guaranteeing that social_class, gender, water_availability, etc. are mathematically
    isolated from the prediction algorithm.
    """
    if not primary_business or not isinstance(primary_business, str):
        return ARCHETYPES[0]
        
    normalized = primary_business.strip().lower()
    
    cluster_id = LIVELIHOOD_DICTIONARY.get(normalized, 0)
    
    return ARCHETYPES[cluster_id]
