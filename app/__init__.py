from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import markdown
from flask import Flask, abort, render_template, send_file
from markupsafe import Markup

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "generated" / "use_cases.json"
DOC_PAGE_CONFIG = {
    "training": {
        "title": "Training Guide",
        "description": "The full hand-held tutorial for all twenty scientific workflows.",
        "path": ROOT / "docs" / "tutorial" / "REAL_DATA_TRAINING_TUTORIAL.md",
    },
    "publication": {
        "title": "Publication Workflow",
        "description": "How authors move from final figure to manuscript and submission bundle.",
        "path": ROOT / "docs" / "PUBLICATION_WORKFLOW.md",
    },
    "architecture": {
        "title": "Architecture",
        "description": "How the service, generator, and artifact pipeline fit together.",
        "path": ROOT / "docs" / "ARCHITECTURE.md",
    },
    "deployment": {
        "title": "Deployment",
        "description": "Local run, Docker, and operational regeneration steps.",
        "path": ROOT / "docs" / "DEPLOYMENT.md",
    },
}


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            "Generated manifest missing. Run `./.venv/bin/python scripts/build_examples.py` first."
        )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_doc_page(slug: str) -> dict:
    if slug not in DOC_PAGE_CONFIG:
        raise KeyError(slug)
    entry = DOC_PAGE_CONFIG[slug]
    markdown_text = entry["path"].read_text(encoding="utf-8")
    html = markdown.markdown(
        markdown_text,
        extensions=["extra", "fenced_code", "tables", "toc", "sane_lists"],
    )
    return {
        "slug": slug,
        "title": entry["title"],
        "description": entry["description"],
        "html": Markup(html),
    }


def safe_resolve(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    if ROOT not in candidate.parents and candidate != ROOT:
        raise ValueError("Requested path is outside the project root.")
    return candidate


def make_brand_mark(name: str) -> str:
    capitals = "".join(char for char in name if char.isupper())
    if len(capitals) >= 2:
        return capitals[:2]
    tokens = [token[0] for token in name.split() if token]
    if len(tokens) >= 2:
        return "".join(tokens[:2]).upper()
    return name[:2].upper()


def find_by_slug(items: list[dict], slug: str) -> dict | None:
    return next((item for item in items if item["slug"] == slug), None)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.context_processor
    def inject_globals() -> dict:
        manifest = load_manifest()
        return {
            "product_name": manifest["product_name"],
            "brand_mark": make_brand_mark(manifest["product_name"]),
            "doc_pages": [{"slug": slug, "title": item["title"]} for slug, item in DOC_PAGE_CONFIG.items()],
        }

    @app.get("/")
    def index():
        manifest = load_manifest()
        use_cases = manifest["use_cases"]
        featured_cases = [use_cases[0], use_cases[11], use_cases[14]]
        hero_stats = [
            ("20", "scientific workflows"),
            ("4", "export formats per figure"),
            ("1", "bundle click to manuscript assets"),
            ("100%", "real datasets"),
        ]
        feature_groups = [
            {
                "title": "Publication-first figures",
                "body": "Vector-ready charts, multi-panel boards, and exports designed for Word, LaTeX, Illustrator, and journal portals.",
            },
            {
                "title": "Guided, trustworthy analysis",
                "body": "Transparent statistical workflows with result summaries, source data, and manuscript drafting text built in.",
            },
            {
                "title": "Fast from data to draft",
                "body": "Each analysis ships with SVG, PDF, PNG, TIFF, caption text, methods text, results text, and a submission checklist.",
            },
        ]
        publication_steps = [
            "Run or open the analysis in the workspace.",
            "Download the manuscript bundle from the figure page.",
            "Insert the SVG or PDF in the manuscript and adapt the included drafting text.",
        ]
        return render_template(
            "landing.html",
            manifest=manifest,
            hero_stats=hero_stats,
            featured_cases=featured_cases,
            feature_groups=feature_groups,
            publication_steps=publication_steps,
        )

    @app.get("/workspace")
    def workspace():
        manifest = load_manifest()
        return render_template("workspace.html", manifest=manifest, workspace=manifest["workspace"])

    @app.get("/projects/<slug>")
    def project_detail(slug: str):
        manifest = load_manifest()
        workspace = manifest["workspace"]
        project = find_by_slug(workspace["projects"], slug)
        if not project:
            abort(404)
        manuscript = find_by_slug(workspace["manuscripts"], project["manuscript_slug"]) if project["manuscript_slug"] else None
        return render_template("project_detail.html", manifest=manifest, project=project, manuscript=manuscript)

    @app.get("/datasets/<slug>")
    def dataset_detail(slug: str):
        manifest = load_manifest()
        workspace = manifest["workspace"]
        dataset = find_by_slug(workspace["datasets"], slug)
        if not dataset:
            abort(404)
        return render_template("dataset_detail.html", manifest=manifest, dataset=dataset)

    @app.get("/manuscripts/<slug>")
    def manuscript_detail(slug: str):
        manifest = load_manifest()
        workspace = manifest["workspace"]
        manuscript = find_by_slug(workspace["manuscripts"], slug)
        if not manuscript:
            abort(404)
        project = find_by_slug(workspace["projects"], manuscript["project_slug"])
        return render_template("manuscript_detail.html", manifest=manifest, manuscript=manuscript, project=project)

    @app.get("/figures/<slug>")
    def figure_detail(slug: str):
        manifest = load_manifest()
        workspace = manifest["workspace"]
        figure = find_by_slug(workspace["figure_drafts"], slug)
        if not figure:
            abort(404)
        project = find_by_slug(workspace["projects"], figure["project_slug"])
        manuscript = find_by_slug(workspace["manuscripts"], figure["manuscript_slug"]) if figure["manuscript_slug"] else None
        return render_template("figure_detail.html", manifest=manifest, figure=figure, project=project, manuscript=manuscript)

    @app.get("/tutorial")
    def tutorial():
        manifest = load_manifest()
        return render_template("tutorial.html", manifest=manifest, use_cases=manifest["use_cases"])

    @app.get("/docs")
    @app.get("/docs/<slug>")
    def docs_page(slug: str = "training"):
        manifest = load_manifest()
        if slug not in DOC_PAGE_CONFIG:
            abort(404)
        selected = load_doc_page(slug)
        pages = [load_doc_page(page_slug) for page_slug in DOC_PAGE_CONFIG]
        return render_template("docs.html", manifest=manifest, selected_doc=selected, doc_pages=pages)

    @app.get("/use-cases/<slug>")
    def use_case(slug: str):
        manifest = load_manifest()
        cases = manifest["use_cases"]
        item = next((case for case in cases if case["slug"] == slug), None)
        if not item:
            abort(404)
        index = item["order"] - 1
        previous_item = cases[index - 1] if index > 0 else None
        next_item = cases[index + 1] if index < len(cases) - 1 else None
        return render_template(
            "use_case.html",
            item=item,
            manifest=manifest,
            previous_item=previous_item,
            next_item=next_item,
        )

    @app.get("/download/<path:relative_path>")
    def download(relative_path: str):
        target = safe_resolve(relative_path)
        if not target.exists():
            abort(404)
        return send_file(target, as_attachment=True)

    @app.get("/assets/<path:relative_path>")
    def asset(relative_path: str):
        target = safe_resolve(f"assets/{relative_path}")
        if not target.exists():
            abort(404)
        return send_file(target)

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "manifest": MANIFEST_PATH.exists()}

    return app
