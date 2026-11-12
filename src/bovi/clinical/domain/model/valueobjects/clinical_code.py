from dataclasses import dataclass

from bovi.shared.domain.exceptions import ValidationError

MESH_SYSTEM = "http://id.nlm.nih.gov/mesh"
NCBI_TAXON_SYSTEM = "http://purl.obolibrary.org/obo/NCBITaxon"
SYSTEMS = frozenset({MESH_SYSTEM, NCBI_TAXON_SYSTEM})


@dataclass(frozen=True, slots=True)
class ClinicalCode:
    """A FHIR-like Coding: MeSH for the disease, NCBI Taxonomy for its agent (RF4)."""

    system: str
    code: str
    display: str

    def __post_init__(self) -> None:
        if self.system not in SYSTEMS:
            raise ValidationError(
                "El código clínico debe ser de MeSH o NCBI Taxonomy.", code="codigo_invalido"
            )
        if not 1 <= len(self.code) <= 20 or not 1 <= len(self.display) <= 120:
            raise ValidationError("El código clínico está incompleto.", code="codigo_invalido")

    def to_json(self) -> dict[str, str]:
        return {"system": self.system, "code": self.code, "display": self.display}
