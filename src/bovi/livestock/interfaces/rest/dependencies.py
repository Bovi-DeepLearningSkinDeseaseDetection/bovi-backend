"""Composition root of the livestock context."""

from fastapi import Depends
from sqlalchemy.orm import Session

from bovi.livestock.application.internal.commandservices.animal_command_service import (
    AnimalCommandService,
)
from bovi.livestock.application.internal.queryservices.animal_query_service import (
    AnimalQueryService,
)
from bovi.livestock.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_animal_repository import (  # noqa: E501
    SqlAlchemyAnimalRepository,
)
from bovi.shared.infrastructure.configuration.settings import Settings, get_app_settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import get_session
from bovi.shared.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_unit_of_work import (  # noqa: E501
    SqlAlchemyUnitOfWork,
)


def get_animal_command_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> AnimalCommandService:
    return AnimalCommandService(
        animals=SqlAlchemyAnimalRepository(session),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        max_batch=settings.sync_max_animals,
    )


def get_animal_query_service(session: Session = Depends(get_session)) -> AnimalQueryService:
    return AnimalQueryService(animals=SqlAlchemyAnimalRepository(session))
