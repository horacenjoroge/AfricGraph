"""Person DataLoader."""
from typing import List
from strawberry.dataloader import DataLoader

from src.domain.models.person import Person
from src.graphql.types.person import PersonType
from src.infrastructure.database.neo4j_client import neo4j_client


async def load_persons(keys: List[str]) -> List[PersonType]:
    """Load multiple persons by ID."""
    persons = []
    for person_id in keys:
        node = neo4j_client.find_node("Person", {"id": person_id})
        if node:
            person = Person.from_node_properties(node)
            persons.append(PersonType.from_domain(person))
        else:
            persons.append(None)
    return persons


def create_person_loader() -> DataLoader[str, PersonType]:
    """Create person DataLoader instance."""
    return DataLoader(load_fn=load_persons)
