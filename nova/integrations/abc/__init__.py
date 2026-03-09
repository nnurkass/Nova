"""ABC PDF/JSON adapter with compatibility aliases for future XML support."""

from nova.integrations.abc.models import (
    ABCMaterial,
    ABCWork,
    EstimateDocumentMeta,
    EstimatePosition,
    ResourceStatement,
)
from nova.integrations.abc.reader import read_abc_document, read_abc_xml
from nova.integrations.abc.writer import (
    deserialize_abc_statement,
    serialize_abc_statement,
    write_abc_statement,
    write_abc_xml,
)

__all__ = [
    "ABCMaterial",
    "ABCWork",
    "EstimateDocumentMeta",
    "EstimatePosition",
    "ResourceStatement",
    "deserialize_abc_statement",
    "read_abc_document",
    "read_abc_xml",
    "serialize_abc_statement",
    "write_abc_statement",
    "write_abc_xml",
]
