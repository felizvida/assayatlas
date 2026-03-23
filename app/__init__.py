from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, render_template, request, send_file

from app.content import ContentService, DownloadPolicy
from app.runtime import WorkspaceService


def create_app(
    content_service: ContentService | None = None,
    download_policy: DownloadPolicy | None = None,
    workspace_service: WorkspaceService | None = None,
) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    service = content_service or ContentService(workspace_service=workspace_service)
    downloads = download_policy or DownloadPolicy()

    @app.context_processor
    def inject_globals() -> dict:
        site = service.site_globals()
        return {
            "product_name": site.product_name,
            "brand_mark": site.brand_mark,
            "doc_pages": site.doc_pages,
        }

    @app.get("/")
    def index():
        page = service.landing_page()
        return render_template(
            "landing.html",
            featured_cases=page.featured_cases,
            hero_stats=page.hero_stats,
            feature_groups=page.feature_groups,
            publication_steps=page.publication_steps,
        )

    @app.get("/workspace")
    def workspace():
        page = service.workspace_page()
        return render_template("workspace.html", workspace=page.workspace)

    @app.get("/projects/<slug>")
    def project_detail(slug: str):
        page = service.project_page(slug)
        if not page:
            abort(404)
        return render_template("project_detail.html", project=page.project, manuscript=page.manuscript)

    @app.get("/datasets/<slug>")
    def dataset_detail(slug: str):
        page = service.dataset_page(slug)
        if not page:
            abort(404)
        return render_template("dataset_detail.html", dataset=page.dataset)

    @app.get("/manuscripts/<slug>")
    def manuscript_detail(slug: str):
        page = service.manuscript_page(slug)
        if not page:
            abort(404)
        return render_template("manuscript_detail.html", manuscript=page.manuscript, project=page.project)

    @app.get("/figures/<slug>")
    def figure_detail(slug: str):
        page = service.figure_page(slug)
        if not page:
            abort(404)
        return render_template(
            "figure_detail.html",
            figure=page.figure,
            project=page.project,
            manuscript=page.manuscript,
        )

    @app.get("/tutorial")
    def tutorial():
        page = service.tutorial_page()
        return render_template("tutorial.html", use_cases=page.use_cases)

    @app.get("/docs")
    @app.get("/docs/<slug>")
    def docs_page(slug: str = "training"):
        page = service.docs_page(slug)
        if not page:
            abort(404)
        return render_template("docs.html", selected_doc=page.selected_doc, doc_pages=page.doc_pages)

    @app.get("/use-cases/<slug>")
    def use_case(slug: str):
        page = service.use_case_page(slug)
        if not page:
            abort(404)
        return render_template(
            "use_case.html",
            item=page.item,
            previous_item=page.previous_item,
            next_item=page.next_item,
        )

    @app.get("/download/<path:relative_path>")
    def download(relative_path: str):
        try:
            target = downloads.resolve_download(relative_path)
        except (FileNotFoundError, PermissionError, ValueError):
            abort(404)
        return send_file(target, as_attachment=True)

    @app.get("/assets/<path:relative_path>")
    def asset(relative_path: str):
        try:
            target = downloads.resolve_asset(relative_path)
        except (FileNotFoundError, PermissionError, ValueError):
            abort(404)
        return send_file(target)

    @app.get("/favicon.ico")
    def favicon():
        return send_file(Path(app.static_folder) / "favicon.svg", mimetype="image/svg+xml")

    @app.get("/healthz")
    def healthz():
        manifest_exists = service.repository.manifest_path.exists()
        workspace_db_exists = service.workspace_service.repository.db_path.exists()
        return {
            "ok": True,
            "manifest": manifest_exists,
            "workspace_db": workspace_db_exists,
            "workspace_schema_version": service.workspace_service.schema_version(),
        }

    @app.get("/api/workspace")
    def api_workspace():
        page = service.workspace_page()
        return page.workspace

    @app.get("/api/projects/<slug>")
    def api_project_detail(slug: str):
        page = service.project_page(slug)
        if not page:
            abort(404)
        return {"project": page.project, "manuscript": page.manuscript}

    @app.get("/api/figures/<slug>")
    def api_figure_detail(slug: str):
        page = service.figure_page(slug)
        if not page:
            abort(404)
        return {"figure": page.figure, "project": page.project, "manuscript": page.manuscript}

    @app.get("/api/datasets/<slug>")
    def api_dataset_detail(slug: str):
        page = service.dataset_page(slug)
        if not page:
            abort(404)
        return {"dataset": page.dataset}

    @app.get("/api/manuscripts/<slug>")
    def api_manuscript_detail(slug: str):
        page = service.manuscript_page(slug)
        if not page:
            abort(404)
        return {"manuscript": page.manuscript, "project": page.project}

    @app.patch("/api/projects/<slug>")
    def api_project_update(slug: str):
        service.ensure_runtime_seeded()
        payload = request.get_json(silent=True) or {}
        allowed_fields = {
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
        changes = {key: value for key, value in payload.items() if key in allowed_fields}
        if not changes:
            return {"error": "No updatable fields provided."}, 400
        project = service.workspace_service.update_project(slug, changes)
        if not project:
            abort(404)
        return {"project": project}

    @app.patch("/api/datasets/<slug>")
    def api_dataset_update(slug: str):
        service.ensure_runtime_seeded()
        payload = request.get_json(silent=True) or {}
        allowed_fields = {
            "name",
            "kind",
            "source",
            "description",
            "updated_at",
        }
        changes = {key: value for key, value in payload.items() if key in allowed_fields}
        if not changes:
            return {"error": "No updatable fields provided."}, 400
        dataset = service.workspace_service.update_dataset(slug, changes)
        if not dataset:
            abort(404)
        return {"dataset": dataset}

    @app.patch("/api/figures/<slug>")
    def api_figure_update(slug: str):
        service.ensure_runtime_seeded()
        payload = request.get_json(silent=True) or {}
        allowed_fields = {
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
        changes = {key: value for key, value in payload.items() if key in allowed_fields}
        if not changes:
            return {"error": "No updatable fields provided."}, 400
        figure = service.workspace_service.update_figure(slug, changes)
        if not figure:
            abort(404)
        return {"figure": figure}

    @app.patch("/api/manuscripts/<slug>")
    def api_manuscript_update(slug: str):
        service.ensure_runtime_seeded()
        payload = request.get_json(silent=True) or {}
        allowed_fields = {
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
        changes = {key: value for key, value in payload.items() if key in allowed_fields}
        if not changes:
            return {"error": "No updatable fields provided."}, 400
        manuscript = service.workspace_service.update_manuscript(slug, changes)
        if not manuscript:
            abort(404)
        return {"manuscript": manuscript}

    @app.get("/api/export-jobs")
    def api_export_jobs():
        service.ensure_runtime_seeded()
        return {"export_jobs": service.workspace_service.list_export_jobs()}

    @app.post("/api/export-jobs")
    def api_export_job_create():
        service.ensure_runtime_seeded()
        payload = request.get_json(silent=True) or {}
        try:
            job = service.workspace_service.create_export_job(payload)
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return {"export_job": job}, 201

    @app.patch("/api/export-jobs/<job_key>")
    def api_export_job_update(job_key: str):
        service.ensure_runtime_seeded()
        payload = request.get_json(silent=True) or {}
        allowed_fields = {"title", "status", "tone", "detail", "path"}
        changes = {key: value for key, value in payload.items() if key in allowed_fields}
        if not changes:
            return {"error": "No updatable fields provided."}, 400
        job = service.workspace_service.update_export_job(job_key, changes)
        if not job:
            abort(404)
        return {"export_job": job}

    @app.get("/api/workspace-events")
    def api_workspace_events():
        service.ensure_runtime_seeded()
        return {"events": service.workspace_service.list_workspace_events()}

    return app
