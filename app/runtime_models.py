from __future__ import annotations

from dataclasses import MISSING, asdict, dataclass, field, fields
from typing import Any, TypeVar

RecordType = TypeVar("RecordType", bound="RuntimePayloadModel")


class RuntimePayloadModel:
    @classmethod
    def from_payload(cls: type[RecordType], payload: dict[str, Any]) -> RecordType:
        values: dict[str, Any] = {}
        declared_names = {field_definition.name for field_definition in fields(cls)}
        for field_definition in fields(cls):
            if field_definition.name == "extras":
                continue
            if field_definition.name in payload:
                values[field_definition.name] = payload[field_definition.name]
                continue
            if field_definition.default is not MISSING:
                values[field_definition.name] = field_definition.default
                continue
            if field_definition.default_factory is not MISSING:
                values[field_definition.name] = field_definition.default_factory()
                continue
            raise KeyError(f"Missing required field '{field_definition.name}' for {cls.__name__}")

        if "extras" in declared_names:
            values["extras"] = {
                key: value
                for key, value in payload.items()
                if key not in declared_names or key == "extras"
            }

        return cls(**values)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        extras = payload.pop("extras", {})
        payload.update(extras)
        return payload

    def merged(self: RecordType, changes: dict[str, Any]) -> RecordType:
        payload = self.to_payload()
        payload.update(changes)
        return type(self).from_payload(payload)


@dataclass(frozen=True)
class ProjectRecord(RuntimePayloadModel):
    slug: str
    name: str
    status: str = ""
    tone: str = ""
    summary: str = ""
    hero_chart_path: str = ""
    completion: int = 0
    figure_count: int = 0
    dataset_count: int = 0
    next_review: str = ""
    team: list[dict[str, Any]] = field(default_factory=list)
    due_date: str = ""
    target_journal: str = ""
    owner: str = ""
    export_preset: str = ""
    tasks: list[str] = field(default_factory=list)
    milestones: list[dict[str, Any]] = field(default_factory=list)
    figures: list[dict[str, Any]] = field(default_factory=list)
    datasets: list[dict[str, Any]] = field(default_factory=list)
    manuscript_slug: str | None = None
    primary_figure_slug: str | None = None
    extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DatasetRecord(RuntimePayloadModel):
    slug: str
    name: str
    path: str = ""
    kind: str = ""
    source: str = ""
    description: str = ""
    rows: int = 0
    columns: int = 0
    updated_at: str = ""
    preview: list[dict[str, Any]] = field(default_factory=list)
    linked_figures: list[dict[str, Any]] = field(default_factory=list)
    linked_projects: list[dict[str, Any]] = field(default_factory=list)
    project_count: int = 0
    figure_count: int = 0
    extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class FigureDraftRecord(RuntimePayloadModel):
    slug: str
    title: str
    chart_path: str = ""
    status: str = ""
    tone: str = ""
    version: str = ""
    summary: str = ""
    project_name: str = ""
    project_slug: str = ""
    manuscript_slug: str | None = None
    what_to_notice: str = ""
    analysis: str = ""
    key_metrics: list[str] = field(default_factory=list)
    publication_assets: dict[str, str] = field(default_factory=dict)
    source_note: str = ""
    caption_text: str = ""
    methods_text: str = ""
    results_text: str = ""
    data_preview: list[dict[str, Any]] = field(default_factory=list)
    next_action: str = ""
    owner: str = ""
    extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ManuscriptPacketRecord(RuntimePayloadModel):
    slug: str
    title: str
    status: str = ""
    tone: str = ""
    narrative: str = ""
    submission_preset: str = ""
    target_journal: str = ""
    due_date: str = ""
    project_slug: str = ""
    project_name: str = ""
    figures: list[dict[str, Any]] = field(default_factory=list)
    datasets: list[dict[str, Any]] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    deliverables: list[dict[str, Any]] = field(default_factory=list)
    figure_progress: str = ""
    extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ExportJobRecord(RuntimePayloadModel):
    title: str
    detail: str
    path: str
    status: str = "Queued"
    tone: str = "warning"
    job_key: str = ""
    extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ActivityItemRecord(RuntimePayloadModel):
    title: str
    meta: str
    path: str
    kind: str
    feed_key: str = ""
    extras: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class WorkspaceEventRecord(RuntimePayloadModel):
    event_type: str
    subject_key: str
    created_at: str
    payload: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict, repr=False)
