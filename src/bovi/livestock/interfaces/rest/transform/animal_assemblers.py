from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.interfaces.rest.resources.animal_resources import (
    AnimalPageResource,
    AnimalResource,
)
from bovi.shared.domain.model.valueobjects.page import Page


def to_animal_page_resource(page: Page[Animal]) -> AnimalPageResource:
    return AnimalPageResource(
        items=[
            AnimalResource(
                id=a.id,
                ear_tag=a.ear_tag.value,
                breed=a.breed,
                sex=a.sex,
                created_at=a.created_at,
            )
            for a in page.items
        ],
        total=page.total,
        next_cursor=page.next_cursor,
    )
