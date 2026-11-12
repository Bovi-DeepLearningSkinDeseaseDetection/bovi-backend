"""History of the farmer to restore it on a new phone (HU13, RF13)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bovi.clinical.domain.model.aggregates.evaluation import Evaluation
from bovi.clinical.domain.model.queries.get_evaluation_history_query import (
    GetEvaluationHistoryQuery,
)
from bovi.clinical.domain.repositories.evaluation_repository import EvaluationRepository
from bovi.clinical.domain.services.image_storage import ImageStorage, PresignedDownload
from bovi.shared.domain.model.valueobjects.page import (
    Page,
    check_limit,
    decode_cursor,
    encode_cursor,
    invalid_cursor,
)


@dataclass(frozen=True, slots=True)
class EvaluationWithImage:
    evaluation: Evaluation
    image: PresignedDownload


class EvaluationQueryService:
    def __init__(self, *, evaluations: EvaluationRepository, storage: ImageStorage) -> None:
        self._evaluations = evaluations
        self._storage = storage

    def get_history(self, query: GetEvaluationHistoryQuery) -> Page[EvaluationWithImage]:
        """One page, newest first, each evaluation with the URL of its photo.

        Presigning is computed locally (no call to S3), so a page of 100 photos costs
        the same as one: restoring 200 evaluations takes 2 to 4 requests (HU13, scenario 2).
        Only the farmer's own evaluations: the user id comes from the token (scenario 3).
        """
        limit = check_limit(query.limit)
        before = self._decode(query.cursor) if query.cursor else None
        rows = self._evaluations.page_for_user(query.user_id, before, limit + 1)
        items = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = items[-1]
            next_cursor = encode_cursor({"at": last.evaluated_at.isoformat(), "id": str(last.id)})
        return Page(
            [EvaluationWithImage(e, self._storage.presign_download(e.image_key)) for e in items],
            self._evaluations.count_for_user(query.user_id),
            next_cursor,
        )

    @staticmethod
    def _decode(cursor: str) -> tuple[datetime, UUID]:
        values = decode_cursor(cursor)
        try:
            at = datetime.fromisoformat(values["at"])
            evaluation_id = UUID(values["id"])
        except (KeyError, TypeError, ValueError) as error:
            raise invalid_cursor() from error
        if at.tzinfo is None:
            raise invalid_cursor()
        return at, evaluation_id
