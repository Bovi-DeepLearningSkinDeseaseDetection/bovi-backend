from typing import Protocol


class UnitOfWork(Protocol):
    """Ends a use case: everything it changed is saved together or not at all."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
