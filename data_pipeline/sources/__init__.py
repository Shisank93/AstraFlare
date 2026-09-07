"""
AstraFlare Multi-Source Data Ingestion & Event Schema Architecture.
Exposes modular adapters for NASA FIRMS, GFW, Government registries, Industrial databases, and Weather services.
"""
from data_pipeline.sources.normalized_event import NormalizedEvent, ProvenanceStatus, LabelProvenance
from data_pipeline.sources.circularity_auditor import circularity_auditor

__all__ = [
    "NormalizedEvent",
    "ProvenanceStatus",
    "LabelProvenance",
    "circularity_auditor",
]
