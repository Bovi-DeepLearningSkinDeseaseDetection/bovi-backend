from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.domain.model.queries.get_animals_query import GetAnimalsQuery
from bovi.livestock.domain.repositories.animal_repository import AnimalRepository
from bovi.shared.domain.model.valueobjects.page import (
    Page,
    check_limit,
    decode_cursor,
    encode_cursor,
    invalid_cursor,
)


class AnimalQueryService:
    def __init__(self, *, animals: AnimalRepository) -> None:
        self._animals = animals

    def get_animals(self, query: GetAnimalsQuery) -> Page[Animal]:
        """Only the farmer's own animals: the user id comes from the token (HU13, scenario 3)."""
        limit = check_limit(query.limit)
        after = None
        if query.cursor:
            after = decode_cursor(query.cursor).get("tag")
            if not isinstance(after, str):
                raise invalid_cursor()
        rows = self._animals.page_for_user(query.user_id, after, limit + 1)
        items = rows[:limit]
        next_cursor = encode_cursor({"tag": items[-1].ear_tag.value}) if len(rows) > limit else None
        return Page(items, self._animals.count_for_user(query.user_id), next_cursor)
