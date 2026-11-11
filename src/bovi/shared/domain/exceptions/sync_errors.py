from bovi.shared.domain.exceptions.domain_error import ValidationError


def check_batch_size(size: int, limit: int, noun: str) -> None:
    """A sync request carries between 1 and `limit` records."""
    if size == 0:
        raise ValidationError(f"Envíe al menos un registro de {noun}.", code="lote_vacio")
    if size > limit:
        raise ValidationError(
            f"Envíe como máximo {limit} registros de {noun} por solicitud.",
            code="lote_muy_grande",
        )
