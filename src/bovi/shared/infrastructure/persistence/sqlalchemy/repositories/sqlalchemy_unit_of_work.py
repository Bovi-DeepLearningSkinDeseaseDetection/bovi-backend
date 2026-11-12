from sqlalchemy.orm import Session


class SqlAlchemyUnitOfWork:
    """UnitOfWork over the session of the request."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
