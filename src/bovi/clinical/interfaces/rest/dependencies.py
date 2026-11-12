"""Composition root of the clinical context."""

from fastapi import Depends
from sqlalchemy.orm import Session

from bovi.clinical.application.acl.livestock_acl import LivestockAcl
from bovi.clinical.application.internal.commandservices.evaluation_command_service import (
    EvaluationCommandService,
)
from bovi.clinical.application.internal.commandservices.media_command_service import (
    MediaCommandService,
)
from bovi.clinical.application.internal.queryservices.evaluation_query_service import (
    EvaluationQueryService,
)
from bovi.clinical.domain.services.image_storage import ImageStorage
from bovi.clinical.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_evaluation_repository import (  # noqa: E501
    SqlAlchemyEvaluationRepository,
)
from bovi.clinical.infrastructure.storage.s3.services.s3_image_storage import S3ImageStorage
from bovi.livestock.interfaces.acl.livestock_context_facade import LivestockContextFacade
from bovi.shared.infrastructure.configuration.settings import Settings, get_app_settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import get_session
from bovi.shared.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_unit_of_work import (  # noqa: E501
    SqlAlchemyUnitOfWork,
)


def get_image_storage(settings: Settings = Depends(get_app_settings)) -> ImageStorage:
    return S3ImageStorage(settings)


def get_media_command_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
    storage: ImageStorage = Depends(get_image_storage),
) -> MediaCommandService:
    return MediaCommandService(
        evaluations=SqlAlchemyEvaluationRepository(session),
        storage=storage,
        max_batch=settings.sync_max_evaluations,
    )


def get_evaluation_command_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
    storage: ImageStorage = Depends(get_image_storage),
) -> EvaluationCommandService:
    return EvaluationCommandService(
        evaluations=SqlAlchemyEvaluationRepository(session),
        livestock=LivestockAcl(LivestockContextFacade(session)),
        storage=storage,
        unit_of_work=SqlAlchemyUnitOfWork(session),
        max_batch=settings.sync_max_evaluations,
        max_image_bytes=settings.s3_max_image_bytes,
    )


def get_evaluation_query_service(
    session: Session = Depends(get_session),
    storage: ImageStorage = Depends(get_image_storage),
) -> EvaluationQueryService:
    return EvaluationQueryService(
        evaluations=SqlAlchemyEvaluationRepository(session), storage=storage
    )
