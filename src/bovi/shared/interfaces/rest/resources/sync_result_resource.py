from uuid import UUID

from pydantic import BaseModel, Field

from bovi.shared.domain.model.valueobjects.sync_result import SyncItemResult, SyncStatus


class SyncItemResultResource(BaseModel):
    id: UUID = Field(description="Id enviado por la app")
    status: SyncStatus
    canonical_id: UUID | None = Field(
        default=None, description="Id con el que quedó guardado (distinto solo si `merged`)"
    )
    code: str | None = Field(default=None, description="Motivo del rechazo, si `rejected`")
    message: str | None = Field(default=None, description="Mensaje en español, si `rejected`")


class SyncBatchResource(BaseModel):
    """Answer of a sync request: one result per record, in the same order."""

    results: list[SyncItemResultResource]
    accepted: int
    duplicates: int
    merged: int
    rejected: int

    @classmethod
    def of(cls, results: list[SyncItemResult]) -> "SyncBatchResource":
        def count(status: SyncStatus) -> int:
            return sum(1 for r in results if r.status is status)

        return cls(
            results=[
                SyncItemResultResource(
                    id=r.id,
                    status=r.status,
                    canonical_id=r.canonical_id,
                    code=r.code,
                    message=r.message,
                )
                for r in results
            ],
            accepted=count(SyncStatus.ACCEPTED),
            duplicates=count(SyncStatus.DUPLICATE),
            merged=count(SyncStatus.MERGED),
            rejected=count(SyncStatus.REJECTED),
        )
