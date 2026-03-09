"""
Metadata Mapper — Tenant-Specific Label Configuration.

Provides TenantConfig (schema) and MetadataMapper / ConfigService
classes that translate internal EVOLV terminology into client-
visible display labels, enabling seamless process mimicry for
enterprise tenants without changing any backend logic.

:requirement: URS-22.1 - System shall support tenant-specific
              metadata label configuration.
:requirement: URS-22.2 - Labels must be applied in UI and
              AI-generated exports.
:requirement: URS-22.3 - Nomenclature map must be loadable from
              a JSON file or named preset at runtime.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


# -----------------------------------------------------------------
# Default internal-key → display-label registry
# -----------------------------------------------------------------
_DEFAULT_LABELS: Dict[str, str] = {
    "requirement":         "Requirement",
    "test_case":           "Test Case",
    "audit":               "Audit",
    "review":              "Review",
    "risk":                "Risk",
    "urs":                 "URS",
    "ur":                  "User Requirement",
    "fr":                  "Functional Requirement",
    "validation_report":   "Validation Report",
    "test_script":         "Test Script",
    "gap_analysis":        "Gap Analysis",
    "traceability_matrix": "Traceability Matrix",
    "compliance_review":   "Compliance Review",
    "change_request":      "Change Request",
    "impact_assessment":   "Impact Assessment",
    "approval":            "Approval",
    "deviation":           "Deviation",
    "capa":                "CAPA",
    "sop":                 "SOP",
    "vendor_doc":          "Vendor Document",
    "validation_factory":  "Validation Factory",
    "smart_requirement":   "SMART Requirement",
    "acceptance_criteria": "Acceptance Criteria",
}

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PRESETS_DIR = _PROJECT_ROOT / "configs" / "nomenclature_maps"


# -----------------------------------------------------------------
# TenantConfig dataclass
# -----------------------------------------------------------------

@dataclass
class TenantConfig:
    """
    Schema for a single tenant's nomenclature and context.

    Holds client-specific display labels, industry, compliance
    mode, and optional SOP guidelines.

    :requirement: URS-22.1 - Tenant-specific label configuration.
    """

    tenant_id: str = "default"
    tenant_name: str = "Default Tenant"
    # pharma | medtech | biotech | clinical | other
    industry: str = "pharma"
    # GMP | GCP | GLP | ISO13485
    compliance_mode: str = "GMP"
    labels: Dict[str, str] = field(default_factory=dict)
    # Client SOP guidelines injected into AI prompts (Task 4)
    sop_guidelines: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "tenant_id":      self.tenant_id,
            "tenant_name":    self.tenant_name,
            "industry":       self.industry,
            "compliance_mode": self.compliance_mode,
            "labels":         self.labels,
            "sop_guidelines": self.sop_guidelines,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantConfig":
        """Deserialise from a plain dictionary."""
        return cls(
            tenant_id=data.get("tenant_id", "default"),
            tenant_name=data.get("tenant_name", "Default Tenant"),
            industry=data.get("industry", "pharma"),
            compliance_mode=data.get("compliance_mode", "GMP"),
            labels=data.get("labels", {}),
            sop_guidelines=data.get("sop_guidelines", ""),
        )


# -----------------------------------------------------------------
# MetadataMapper
# -----------------------------------------------------------------

class MetadataMapper:
    """
    Translates internal EVOLV keys to client-visible labels.

    Falls back gracefully to the default EVOLV label when no
    tenant override exists, so all callers are always safe to
    call ``mapper.label("requirement")`` unconditionally.

    :requirement: URS-22.1 - Tenant-specific metadata label
                  configuration.
    :requirement: URS-22.2 - Labels applied in UI and exports.
    """

    def __init__(
        self,
        config: Optional[TenantConfig] = None,
    ) -> None:
        """
        Initialise the mapper.

        :param config: Optional TenantConfig.  When *None*, the
                       default EVOLV labels are used unchanged.
        """
        self._config = config
        self._labels: Dict[str, str] = {
            **_DEFAULT_LABELS,
            **(config.labels if config else {}),
        }

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def label(self, internal_key: str) -> str:
        """
        Return the display label for an internal EVOLV key.

        :param internal_key: Internal key (e.g. "requirement").
        :return: Client-visible display string.
        :requirement: URS-22.1
        """
        return self._labels.get(
            internal_key,
            internal_key.replace("_", " ").title(),
        )

    def apply(self, text: str) -> str:
        """
        Replace default EVOLV labels in *text* with their
        client-specific equivalents (whole-word, case-insensitive).

        Only overridden labels are substituted; unchanged labels
        are left as-is.

        :param text: Source string (AI-generated output, etc.).
        :return: String with client labels substituted.
        :requirement: URS-22.2
        """
        result = text
        for key, display in self._labels.items():
            default = _DEFAULT_LABELS.get(key, "")
            if default and default.lower() != display.lower():
                result = re.sub(
                    r"\b" + re.escape(default) + r"\b",
                    display,
                    result,
                    flags=re.IGNORECASE,
                )
        return result

    def get_all_labels(self) -> Dict[str, str]:
        """Return a copy of the full label dictionary."""
        return dict(self._labels)

    @property
    def config(self) -> Optional[TenantConfig]:
        """Return the underlying TenantConfig (may be None)."""
        return self._config

    # ----------------------------------------------------------
    # Constructors
    # ----------------------------------------------------------

    @classmethod
    def from_json(cls, path: str) -> "MetadataMapper":
        """
        Load a MetadataMapper from a JSON nomenclature-map file.

        The JSON must contain a ``labels`` dict.  All other
        TenantConfig fields are optional.

        :param path: Path to the JSON file.
        :return: MetadataMapper instance.
        :requirement: URS-22.3
        """
        data = json.loads(
            Path(path).read_text(encoding="utf-8")
        )
        return cls(config=TenantConfig.from_dict(data))

    @classmethod
    def load_preset(cls, preset_name: str) -> "MetadataMapper":
        """
        Load a named preset from ``configs/nomenclature_maps/``.

        :param preset_name: File stem, e.g. "pharma_standard".
        :return: MetadataMapper instance.
        :raises FileNotFoundError: If preset does not exist.
        :requirement: URS-22.3
        """
        path = _PRESETS_DIR / f"{preset_name}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Nomenclature preset '{preset_name}' not "
                f"found at {path}"
            )
        return cls.from_json(str(path))

    @classmethod
    def default(cls) -> "MetadataMapper":
        """Return a mapper with no overrides (EVOLV defaults)."""
        return cls(config=None)


# -----------------------------------------------------------------
# ConfigService — session singleton facade
# -----------------------------------------------------------------

class ConfigService:
    """
    Singleton-style facade that holds the active tenant config
    for the current runtime session.

    Usage::

        svc = ConfigService.get_instance()
        svc.load_from_dict(my_nomenclature_map)
        label = svc.mapper.label("requirement")  # → "User Need"

    :requirement: URS-22.1 - Dynamic nomenclature at runtime.
    """

    _instance: Optional["ConfigService"] = None

    def __init__(self) -> None:
        self._mapper: MetadataMapper = MetadataMapper.default()

    @classmethod
    def get_instance(cls) -> "ConfigService":
        """Return (or create) the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------

    def load_from_dict(
        self, data: Dict[str, Any]
    ) -> "ConfigService":
        """
        Load nomenclature configuration from a dictionary.

        :param data: Dict matching the TenantConfig schema.
        :return: Self, for chaining.
        :requirement: URS-22.1
        """
        self._mapper = MetadataMapper(
            config=TenantConfig.from_dict(data)
        )
        return self

    def load_from_json(self, path: str) -> "ConfigService":
        """
        Load nomenclature configuration from a JSON file.

        :param path: Path to the JSON nomenclature map.
        :return: Self, for chaining.
        :requirement: URS-22.3
        """
        self._mapper = MetadataMapper.from_json(path)
        return self

    def reset(self) -> "ConfigService":
        """Reset to default EVOLV labels."""
        self._mapper = MetadataMapper.default()
        return self

    @property
    def mapper(self) -> MetadataMapper:
        """Return the active MetadataMapper."""
        return self._mapper

    def label(self, key: str) -> str:
        """Shortcut — delegates to mapper.label()."""
        return self._mapper.label(key)

    def apply(self, text: str) -> str:
        """Shortcut — delegates to mapper.apply()."""
        return self._mapper.apply(text)
