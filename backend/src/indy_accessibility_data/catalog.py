"""Typed access to the project data catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_CATALOG_PATH = Path("data/catalog/datasets.json")


class CatalogError(ValueError):
    """Raised when the data catalog is missing or invalid."""


class ProjectGeography(BaseModel):
    """Stable identifiers for the project study area."""

    model_config = ConfigDict(extra="forbid")

    name: str
    state_fips: str = Field(pattern=r"^\d{2}$")
    county_fips: str = Field(pattern=r"^\d{3}$")


class LicenseMetadata(BaseModel):
    """Published terms and cautious interpretation for one source."""

    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    notes: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Require a direct HTTP(S) terms or metadata URL."""
        return _validate_http_url(value)


class ValidationRules(BaseModel):
    """Format-specific minimum checks applied to a cached response."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "census_json",
        "csv_zip",
        "geojson",
        "gtfs_zip",
        "html",
        "shapefile_zip",
        "xlsx",
    ]
    required_fields: list[str] | dict[str, list[str]] | None = None
    required_members: list[str] | None = None
    required_sheets: dict[str, list[str]] | None = None
    required_text: list[str] | None = None
    geometry_types: list[str] | None = None
    minimum_records: int | None = Field(default=None, ge=1)
    minimum_bytes: int | None = Field(default=None, ge=1)
    bounds: tuple[float, float, float, float] | None = None
    field_equals: dict[str, str] | None = None

    @model_validator(mode="after")
    def require_kind_configuration(self) -> ValidationRules:
        """Reject catalog rules that cannot validate their declared format."""
        required_by_kind = {
            "census_json": self.required_fields,
            "csv_zip": self.required_fields,
            "geojson": self.required_fields,
            "gtfs_zip": self.required_members,
            "html": self.required_text,
            "shapefile_zip": self.required_members,
            "xlsx": self.required_sheets,
        }
        if not required_by_kind[self.kind]:
            msg = f"validation kind {self.kind!r} lacks its required configuration"
            raise ValueError(msg)
        return self


class Dataset(BaseModel):
    """Complete acquisition and provenance metadata for one dataset."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
    name: str
    purpose: str
    source_organization: str
    source_page_url: str
    source_url: str
    retrieval_method: Literal[
        "http_get",
        "http_get_html",
        "http_get_subject_to_terms",
        "http_get_with_environment_parameter",
    ]
    requires_environment: list[str] = Field(default_factory=list)
    retrieval_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    license: LicenseMetadata
    geographic_coverage: str
    crs: str
    important_fields: list[str] = Field(min_length=1)
    expected_format: str
    cache_filename: str
    authoritative_status: Literal[
        "authoritative",
        "authoritative_aggregator",
        "authoritative_fallback",
    ]
    known_limitations: list[str] = Field(min_length=1)
    manual_fallback: str
    validation: ValidationRules

    @field_validator("source_page_url", "source_url")
    @classmethod
    def validate_urls(cls, value: str) -> str:
        """Require direct HTTP(S) URLs while permitting environment templates."""
        candidate = value
        for placeholder in ("{CENSUS_API_KEY}",):
            candidate = candidate.replace(placeholder, "placeholder")
        _validate_http_url(candidate)
        return value

    @model_validator(mode="after")
    def require_environment_placeholders(self) -> Dataset:
        """Keep declared environment values aligned with URL placeholders."""
        for variable in self.requires_environment:
            if f"{{{variable}}}" not in self.source_url:
                msg = f"{self.id}: source_url is missing {{{variable}}}"
                raise ValueError(msg)
        if "{" in self.source_url and not self.requires_environment:
            msg = f"{self.id}: source_url has an undeclared environment placeholder"
            raise ValueError(msg)
        return self


class DataCatalog(BaseModel):
    """Versioned collection of project source datasets."""

    model_config = ConfigDict(extra="forbid")

    catalog_version: str = Field(pattern=r"^\d+\.\d+$")
    project_geography: ProjectGeography
    last_verified: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    datasets: list[Dataset] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_ids_and_filenames(self) -> DataCatalog:
        """Prevent two sources from sharing an identifier or cache target."""
        ids = [dataset.id for dataset in self.datasets]
        filenames = [dataset.cache_filename for dataset in self.datasets]
        if len(ids) != len(set(ids)):
            raise ValueError("dataset ids must be unique")
        if len(filenames) != len(set(filenames)):
            raise ValueError("cache filenames must be unique")
        return self

    def dataset(self, dataset_id: str) -> Dataset:
        """Return one dataset or a useful error listing valid choices."""
        for dataset in self.datasets:
            if dataset.id == dataset_id:
                return dataset
        available = ", ".join(item.id for item in self.datasets)
        raise CatalogError(
            f"unknown dataset {dataset_id!r}; available datasets: {available}"
        )


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> DataCatalog:
    """Load and validate the machine-readable catalog."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CatalogError(f"data catalog not found: {path}") from error
    except json.JSONDecodeError as error:
        raise CatalogError(f"data catalog is not valid JSON: {error}") from error

    try:
        return DataCatalog.model_validate(raw)
    except ValueError as error:
        raise CatalogError(f"data catalog validation failed: {error}") from error


def _validate_http_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"expected an HTTP(S) URL, received {value!r}")
    if parsed.username or parsed.password:
        raise ValueError("catalog URLs must not contain credentials")
    return value
