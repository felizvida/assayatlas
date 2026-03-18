from __future__ import annotations

from flask import Flask, abort, render_template, send_file

from app.content import ContentService, DownloadPolicy


def create_app(
    content_service: ContentService | None = None,
    download_policy: DownloadPolicy | None = None,
) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    service = content_service or ContentService()
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

    @app.get("/healthz")
    def healthz():
        manifest_exists = service.repository.manifest_path.exists()
        return {"ok": True, "manifest": manifest_exists}

    return app
