from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bovi.iam.domain.exceptions.iam_errors import EmailAlreadyRegisteredError
from bovi.iam.domain.model.aggregates.user import User
from bovi.iam.domain.model.valueobjects.email_address import EmailAddress
from bovi.iam.domain.model.valueobjects.person_name import PersonName
from bovi.iam.infrastructure.persistence.sqlalchemy.entities.user_entity import UserEntity


def _to_entity(user: User) -> UserEntity:
    return UserEntity(
        id=user.id,
        nombre=user.name.value,
        correo=user.email.value,
        hash_contrasena=user.password_hash,
        activo=user.active,
        consentimiento_aceptado_en=user.consent_accepted_at,
        consentimiento_version=user.consent_version,
        creado_en=user.created_at,
    )


def _to_domain(entity: UserEntity) -> User:
    return User(
        id=entity.id,
        name=PersonName(entity.nombre),
        email=EmailAddress(entity.correo),
        password_hash=entity.hash_contrasena,
        active=entity.activo,
        consent_accepted_at=entity.consentimiento_aceptado_en,
        consent_version=entity.consentimiento_version,
        created_at=entity.creado_en,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(_to_entity(user))
        try:
            # Flush now so a taken e-mail (even in a race) becomes a domain error.
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise EmailAlreadyRegisteredError() from error

    def find_by_id(self, user_id: UUID) -> User | None:
        entity = self._session.get(UserEntity, user_id)
        return _to_domain(entity) if entity else None

    def find_by_email(self, email: EmailAddress) -> User | None:
        entity = self._session.scalar(select(UserEntity).where(UserEntity.correo == email.value))
        return _to_domain(entity) if entity else None
