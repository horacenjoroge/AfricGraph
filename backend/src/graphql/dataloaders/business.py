"""Business DataLoader."""
from typing import List
from strawberry.dataloader import DataLoader

from src.api.services.business import get_business
from src.domain.models.business import Business
from src.graphql.types.business import BusinessType


async def load_businesses(keys: List[str]) -> List[BusinessType]:
    """Load multiple businesses by ID."""
    businesses = []
    for business_id in keys:
        business = get_business(business_id)
        if business:
            businesses.append(BusinessType.from_domain(business))
        else:
            businesses.append(None)
    return businesses


def create_business_loader() -> DataLoader[str, BusinessType]:
    """Create business DataLoader instance."""
    return DataLoader(load_fn=load_businesses)
