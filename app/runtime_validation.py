from __future__ import annotations

from typing import Any, Iterable

PROJECT_CREATE_FIELDS = frozenset(
    {
        "slug",
        "name",
        "status",
        "tone",
        "summary",
        "hero_chart_path",
        "completion",
        "figure_count",
        "dataset_count",
        "next_review",
        "team",
        "due_date",
        "target_journal",
        "owner",
        "export_preset",
        "tasks",
        "milestones",
        "figures",
        "datasets",
        "manuscript_slug",
        "primary_figure_slug",
    }
)
PROJECT_UPDATE_FIELDS = frozenset(
    {
        "name",
        "status",
        "tone",
        "summary",
        "next_review",
        "due_date",
        "completion",
        "owner",
        "target_journal",
        "export_preset",
        "tasks",
        "milestones",
        "team",
    }
)
DATASET_UPDATE_FIELDS = frozenset({"name", "kind", "source", "description", "updated_at"})
FIGURE_UPDATE_FIELDS = frozenset(
    {
        "title",
        "status",
        "tone",
        "version",
        "summary",
        "what_to_notice",
        "key_metrics",
        "caption_text",
        "methods_text",
        "results_text",
        "next_action",
        "owner",
    }
)
MANUSCRIPT_UPDATE_FIELDS = frozenset(
    {
        "title",
        "status",
        "tone",
        "narrative",
        "submission_preset",
        "target_journal",
        "due_date",
        "sections",
        "deliverables",
        "figure_progress",
    }
)
EXPORT_JOB_CREATE_FIELDS = frozenset({"title", "detail", "path", "status", "tone", "job_key"})
EXPORT_JOB_UPDATE_FIELDS = frozenset({"title", "status", "tone", "detail", "path"})

PROJECT_UPDATE_STRING_FIELDS = {
    "name": "Project name",
    "status": "Project status",
    "tone": "Project tone",
    "summary": "Project summary",
    "next_review": "Project next_review",
    "due_date": "Project due_date",
    "owner": "Project owner",
    "target_journal": "Project target_journal",
    "export_preset": "Project export_preset",
}
PROJECT_CREATE_OPTIONAL_STRING_FIELDS = {
    "slug": "Project slug",
    "status": "Project status",
    "tone": "Project tone",
    "summary": "Project summary",
    "hero_chart_path": "Project hero_chart_path",
    "next_review": "Project next_review",
    "due_date": "Project due_date",
    "target_journal": "Project target_journal",
    "owner": "Project owner",
    "export_preset": "Project export_preset",
}
DATASET_UPDATE_STRING_FIELDS = {
    "name": "Dataset name",
    "kind": "Dataset kind",
    "source": "Dataset source",
    "description": "Dataset description",
    "updated_at": "Dataset updated_at",
}
FIGURE_UPDATE_STRING_FIELDS = {
    "title": "Figure title",
    "status": "Figure status",
    "tone": "Figure tone",
    "version": "Figure version",
    "summary": "Figure summary",
    "what_to_notice": "Figure what_to_notice",
    "caption_text": "Figure caption_text",
    "methods_text": "Figure methods_text",
    "results_text": "Figure results_text",
    "next_action": "Figure next_action",
    "owner": "Figure owner",
}
MANUSCRIPT_UPDATE_STRING_FIELDS = {
    "title": "Manuscript title",
    "status": "Manuscript status",
    "tone": "Manuscript tone",
    "narrative": "Manuscript narrative",
    "submission_preset": "Manuscript submission_preset",
    "target_journal": "Manuscript target_journal",
    "due_date": "Manuscript due_date",
    "figure_progress": "Manuscript figure_progress",
}
EXPORT_JOB_REQUIRED_FIELDS = {"title", "detail", "path"}
EXPORT_JOB_STRING_FIELDS = {
    "title": "Export job title",
    "detail": "Export job detail",
    "path": "Export job path",
    "status": "Export job status",
    "tone": "Export job tone",
    "job_key": "Export job job_key",
}


def filter_allowed_fields(payload: dict[str, Any], allowed_fields: Iterable[str]) -> dict[str, Any]:
    allowed = set(allowed_fields)
    return {key: value for key, value in payload.items() if key in allowed}


def require_non_empty_string(value: Any, field_label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_label} must be a non-empty string")
    return value.strip()


def normalize_optional_string(value: Any, field_label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_label} must be a string")
    stripped = value.strip()
    return stripped or None


def normalize_required_string_fields(
    payload: dict[str, Any],
    field_labels: dict[str, str],
) -> dict[str, Any]:
    normalized_payload = dict(payload)
    for field, field_label in field_labels.items():
        if field in normalized_payload:
            normalized_payload[field] = require_non_empty_string(
                normalized_payload[field],
                field_label=field_label,
            )
    return normalized_payload


def normalize_string_list(value: Any, field_label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_label} must be a list of non-empty strings")
    return [require_non_empty_string(item, field_label=f"{field_label} item") for item in value]


def normalize_labeled_state_list(value: Any, field_label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field_label} must be a list of objects")
    normalized_items: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_label} must be a list of objects")
        normalized_item = dict(item)
        normalized_item["label"] = require_non_empty_string(
            item.get("label"),
            field_label=f"{field_label} label",
        )
        normalized_item["state"] = require_non_empty_string(
            item.get("state"),
            field_label=f"{field_label} state",
        )
        normalized_items.append(normalized_item)
    return normalized_items


def normalize_team_list(value: Any, field_label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field_label} must be a list of objects")
    normalized_items: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_label} must be a list of objects")
        normalized_item = dict(item)
        normalized_item["name"] = require_non_empty_string(
            item.get("name"),
            field_label=f"{field_label} name",
        )
        normalized_item["role"] = require_non_empty_string(
            item.get("role"),
            field_label=f"{field_label} role",
        )
        normalized_item["initials"] = require_non_empty_string(
            item.get("initials"),
            field_label=f"{field_label} initials",
        )
        normalized_items.append(normalized_item)
    return normalized_items


def normalize_project_structured_fields(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(payload)
    if "tasks" in normalized_payload:
        normalized_payload["tasks"] = normalize_string_list(
            normalized_payload["tasks"],
            field_label="Project tasks",
        )
    if "milestones" in normalized_payload:
        normalized_payload["milestones"] = normalize_labeled_state_list(
            normalized_payload["milestones"],
            field_label="Project milestones",
        )
    if "team" in normalized_payload:
        normalized_payload["team"] = normalize_team_list(
            normalized_payload["team"],
            field_label="Project team",
        )
    return normalized_payload


def normalize_figure_structured_fields(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(payload)
    if "key_metrics" in normalized_payload:
        normalized_payload["key_metrics"] = normalize_string_list(
            normalized_payload["key_metrics"],
            field_label="Figure key_metrics",
        )
    return normalized_payload


def normalize_manuscript_structured_fields(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(payload)
    if "sections" in normalized_payload:
        normalized_payload["sections"] = normalize_labeled_state_list(
            normalized_payload["sections"],
            field_label="Manuscript sections",
        )
    if "deliverables" in normalized_payload:
        normalized_payload["deliverables"] = normalize_labeled_state_list(
            normalized_payload["deliverables"],
            field_label="Manuscript deliverables",
        )
    return normalized_payload


def normalize_project_create_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(filter_allowed_fields(payload, PROJECT_CREATE_FIELDS))
    normalized_payload["name"] = require_non_empty_string(
        normalized_payload.get("name"),
        field_label="Project name",
    )
    for field, field_label in PROJECT_CREATE_OPTIONAL_STRING_FIELDS.items():
        if field in normalized_payload:
            normalized_value = normalize_optional_string(normalized_payload[field], field_label=field_label)
            if normalized_value is None:
                normalized_payload.pop(field)
            else:
                normalized_payload[field] = normalized_value
    return normalize_project_structured_fields(normalized_payload)


def normalize_project_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = normalize_required_string_fields(
        filter_allowed_fields(payload, PROJECT_UPDATE_FIELDS),
        PROJECT_UPDATE_STRING_FIELDS,
    )
    return normalize_project_structured_fields(normalized_payload)


def normalize_dataset_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return normalize_required_string_fields(
        filter_allowed_fields(payload, DATASET_UPDATE_FIELDS),
        DATASET_UPDATE_STRING_FIELDS,
    )


def normalize_figure_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = normalize_required_string_fields(
        filter_allowed_fields(payload, FIGURE_UPDATE_FIELDS),
        FIGURE_UPDATE_STRING_FIELDS,
    )
    return normalize_figure_structured_fields(normalized_payload)


def normalize_manuscript_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = normalize_required_string_fields(
        filter_allowed_fields(payload, MANUSCRIPT_UPDATE_FIELDS),
        MANUSCRIPT_UPDATE_STRING_FIELDS,
    )
    return normalize_manuscript_structured_fields(normalized_payload)


def normalize_export_job_create_payload(payload: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(EXPORT_JOB_REQUIRED_FIELDS - payload.keys())
    if missing:
        raise ValueError(f"Missing required export job fields: {', '.join(missing)}")
    return normalize_required_string_fields(
        filter_allowed_fields(payload, EXPORT_JOB_CREATE_FIELDS),
        EXPORT_JOB_STRING_FIELDS,
    )


def normalize_export_job_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return normalize_required_string_fields(
        filter_allowed_fields(payload, EXPORT_JOB_UPDATE_FIELDS),
        {
            key: value
            for key, value in EXPORT_JOB_STRING_FIELDS.items()
            if key in EXPORT_JOB_UPDATE_FIELDS
        },
    )
