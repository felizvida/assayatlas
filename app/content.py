from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import markdown
from markupsafe import Markup

from app.runtime import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "generated" / "use_cases.json"


@dataclass(frozen=True)
class DocDescriptor:
    slug: str
    title: str
    description: str
    path: Path


DOC_PAGE_CONFIG: dict[str, DocDescriptor] = {
    "training": DocDescriptor(
        slug="training",
        title="Training Guide",
        description="The full hand-held tutorial for all twenty scientific workflows.",
        path=ROOT / "docs" / "tutorial" / "REAL_DATA_TRAINING_TUTORIAL.md",
    ),
    "publication": DocDescriptor(
        slug="publication",
        title="Publication Workflow",
        description="How authors move from final figure to manuscript and submission bundle.",
        path=ROOT / "docs" / "PUBLICATION_WORKFLOW.md",
    ),
    "architecture": DocDescriptor(
        slug="architecture",
        title="Architecture",
        description="How the service, generator, and artifact pipeline fit together.",
        path=ROOT / "docs" / "ARCHITECTURE.md",
    ),
    "deployment": DocDescriptor(
        slug="deployment",
        title="Deployment",
        description="Local run, Docker, and operational regeneration steps.",
        path=ROOT / "docs" / "DEPLOYMENT.md",
    ),
}


@dataclass(frozen=True)
class DocPageSummary:
    slug: str
    title: str
    description: str


@dataclass(frozen=True)
class DocPage(DocPageSummary):
    html: Markup


@dataclass(frozen=True)
class ManifestSnapshot:
    product_name: str
    summary: str
    use_cases: list[dict[str, Any]]
    workspace: dict[str, Any]
    raw: dict[str, Any] = field(repr=False)
    _use_cases_by_slug: dict[str, dict[str, Any]] = field(repr=False)
    _use_case_positions: dict[str, int] = field(repr=False)
    _projects_by_slug: dict[str, dict[str, Any]] = field(repr=False)
    _datasets_by_slug: dict[str, dict[str, Any]] = field(repr=False)
    _manuscripts_by_slug: dict[str, dict[str, Any]] = field(repr=False)
    _figures_by_slug: dict[str, dict[str, Any]] = field(repr=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ManifestSnapshot":
        use_cases = payload["use_cases"]
        workspace = payload["workspace"]
        return cls(
            product_name=payload["product_name"],
            summary=payload["summary"],
            use_cases=use_cases,
            workspace=workspace,
            raw=payload,
            _use_cases_by_slug={item["slug"]: item for item in use_cases},
            _use_case_positions={item["slug"]: index for index, item in enumerate(use_cases)},
            _projects_by_slug={item["slug"]: item for item in workspace["projects"]},
            _datasets_by_slug={item["slug"]: item for item in workspace["datasets"]},
            _manuscripts_by_slug={item["slug"]: item for item in workspace["manuscripts"]},
            _figures_by_slug={item["slug"]: item for item in workspace["figure_drafts"]},
        )

    def get_use_case(self, slug: str) -> dict[str, Any] | None:
        return self._use_cases_by_slug.get(slug)

    def get_project(self, slug: str) -> dict[str, Any] | None:
        return self._projects_by_slug.get(slug)

    def get_dataset(self, slug: str) -> dict[str, Any] | None:
        return self._datasets_by_slug.get(slug)

    def get_manuscript(self, slug: str) -> dict[str, Any] | None:
        return self._manuscripts_by_slug.get(slug)

    def get_figure(self, slug: str) -> dict[str, Any] | None:
        return self._figures_by_slug.get(slug)

    def adjacent_use_cases(self, slug: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        index = self._use_case_positions.get(slug)
        if index is None:
            return None, None
        previous_item = self.use_cases[index - 1] if index > 0 else None
        next_item = self.use_cases[index + 1] if index < len(self.use_cases) - 1 else None
        return previous_item, next_item


@dataclass(frozen=True)
class SiteGlobals:
    product_name: str
    brand_mark: str
    doc_pages: list[DocPageSummary]


@dataclass(frozen=True)
class LandingPageContext:
    featured_cases: list[dict[str, Any]]
    hero_stats: list[tuple[str, str]]
    feature_groups: list[dict[str, str]]
    publication_steps: list[str]


@dataclass(frozen=True)
class WorkspacePageContext:
    workspace: dict[str, Any]


@dataclass(frozen=True)
class ProjectPageContext:
    project: dict[str, Any]
    manuscript: dict[str, Any] | None


@dataclass(frozen=True)
class DatasetPageContext:
    dataset: dict[str, Any]


@dataclass(frozen=True)
class ManuscriptPageContext:
    manuscript: dict[str, Any]
    project: dict[str, Any]


@dataclass(frozen=True)
class FigurePageContext:
    figure: dict[str, Any]
    project: dict[str, Any]
    manuscript: dict[str, Any] | None


@dataclass(frozen=True)
class TutorialPageContext:
    use_cases: list[dict[str, Any]]


@dataclass(frozen=True)
class DocsPageContext:
    selected_doc: DocPage
    doc_pages: list[DocPageSummary]


@dataclass(frozen=True)
class UseCasePageContext:
    item: dict[str, Any]
    previous_item: dict[str, Any] | None
    next_item: dict[str, Any] | None


def make_brand_mark(name: str) -> str:
    capitals = "".join(char for char in name if char.isupper())
    if len(capitals) >= 2:
        return capitals[:2]
    tokens = [token[0] for token in name.split() if token]
    if len(tokens) >= 2:
        return "".join(tokens[:2]).upper()
    return name[:2].upper()


class FileBackedContentRepository:
    def __init__(
        self,
        manifest_path: Path = MANIFEST_PATH,
        doc_page_config: dict[str, DocDescriptor] = DOC_PAGE_CONFIG,
    ) -> None:
        self.manifest_path = manifest_path
        self.doc_page_config = doc_page_config
        self._manifest_cache: tuple[int, ManifestSnapshot] | None = None
        self._doc_cache: dict[str, tuple[int, DocPage]] = {}

    def manifest(self) -> ManifestSnapshot:
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                "Generated manifest missing. Run `./.venv/bin/python scripts/build_examples.py` first."
            )
        mtime = self.manifest_path.stat().st_mtime_ns
        if self._manifest_cache and self._manifest_cache[0] == mtime:
            return self._manifest_cache[1]
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        snapshot = ManifestSnapshot.from_dict(payload)
        self._manifest_cache = (mtime, snapshot)
        return snapshot

    def doc_page(self, slug: str) -> DocPage:
        descriptor = self.doc_page_config[slug]
        mtime = descriptor.path.stat().st_mtime_ns
        cached = self._doc_cache.get(slug)
        if cached and cached[0] == mtime:
            return cached[1]
        markdown_text = descriptor.path.read_text(encoding="utf-8")
        html = markdown.markdown(
            markdown_text,
            extensions=["extra", "fenced_code", "tables", "toc", "sane_lists"],
        )
        page = DocPage(
            slug=descriptor.slug,
            title=descriptor.title,
            description=descriptor.description,
            html=Markup(html),
        )
        self._doc_cache[slug] = (mtime, page)
        return page

    def doc_page_summaries(self) -> list[DocPageSummary]:
        return [
            DocPageSummary(slug=item.slug, title=item.title, description=item.description)
            for item in self.doc_page_config.values()
        ]


class DownloadPolicy:
    def __init__(
        self,
        root: Path = ROOT,
        allowed_roots: tuple[Path, ...] | None = None,
        allowed_files: tuple[Path, ...] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.allowed_roots = tuple(
            path.resolve()
            for path in (allowed_roots or (self.root / "data" / "generated", self.root / "data" / "raw"))
        )
        self.allowed_files = tuple(
            path.resolve()
            for path in (allowed_files or (self.root / "docs" / "tutorial" / "USE_CASE_CATALOG.md",))
        )
        self.asset_root = (self.root / "assets").resolve()

    def resolve_download(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        self._ensure_under_root(candidate)
        if not candidate.exists():
            raise FileNotFoundError(relative_path)
        if candidate in self.allowed_files:
            return candidate
        if any(root == candidate or root in candidate.parents for root in self.allowed_roots):
            return candidate
        raise PermissionError(relative_path)

    def resolve_asset(self, relative_path: str) -> Path:
        candidate = (self.asset_root / relative_path).resolve()
        self._ensure_under_root(candidate, self.asset_root)
        if not candidate.exists():
            raise FileNotFoundError(relative_path)
        return candidate

    def _ensure_under_root(self, candidate: Path, root: Path | None = None) -> None:
        boundary = root or self.root
        if boundary not in candidate.parents and candidate != boundary:
            raise PermissionError(str(candidate))


class ContentService:
    def __init__(
        self,
        repository: FileBackedContentRepository | None = None,
        workspace_service: WorkspaceService | None = None,
    ) -> None:
        self.repository = repository or FileBackedContentRepository()
        self.workspace_service = workspace_service or WorkspaceService()

    def _ensure_workspace_seeded(self) -> ManifestSnapshot:
        manifest = self.repository.manifest()
        self.workspace_service.ensure_seeded(manifest.workspace)
        return manifest

    def site_globals(self) -> SiteGlobals:
        manifest = self.repository.manifest()
        return SiteGlobals(
            product_name=manifest.product_name,
            brand_mark=make_brand_mark(manifest.product_name),
            doc_pages=self.repository.doc_page_summaries(),
        )

    def landing_page(self) -> LandingPageContext:
        manifest = self.repository.manifest()
        featured_cases = [manifest.use_cases[0], manifest.use_cases[11], manifest.use_cases[14]]
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
        return LandingPageContext(
            featured_cases=featured_cases,
            hero_stats=hero_stats,
            feature_groups=feature_groups,
            publication_steps=publication_steps,
        )

    def workspace_page(self) -> WorkspacePageContext:
        self._ensure_workspace_seeded()
        return WorkspacePageContext(workspace=self.workspace_service.workspace_snapshot())

    def project_page(self, slug: str) -> ProjectPageContext | None:
        manifest = self._ensure_workspace_seeded()
        project = self.workspace_service.get_project(slug) or manifest.get_project(slug)
        if not project:
            return None
        manuscript = (
            self.workspace_service.get_manuscript(project["manuscript_slug"]) or manifest.get_manuscript(project["manuscript_slug"])
            if project["manuscript_slug"]
            else None
        )
        return ProjectPageContext(project=project, manuscript=manuscript)

    def dataset_page(self, slug: str) -> DatasetPageContext | None:
        manifest = self._ensure_workspace_seeded()
        dataset = self.workspace_service.get_dataset(slug) or manifest.get_dataset(slug)
        if not dataset:
            return None
        return DatasetPageContext(dataset=dataset)

    def manuscript_page(self, slug: str) -> ManuscriptPageContext | None:
        manifest = self._ensure_workspace_seeded()
        manuscript = self.workspace_service.get_manuscript(slug) or manifest.get_manuscript(slug)
        if not manuscript:
            return None
        project = self.workspace_service.get_project(manuscript["project_slug"]) or manifest.get_project(manuscript["project_slug"])
        if not project:
            return None
        return ManuscriptPageContext(manuscript=manuscript, project=project)

    def figure_page(self, slug: str) -> FigurePageContext | None:
        manifest = self._ensure_workspace_seeded()
        figure = self.workspace_service.get_figure(slug) or manifest.get_figure(slug)
        if not figure:
            return None
        project = self.workspace_service.get_project(figure["project_slug"]) or manifest.get_project(figure["project_slug"])
        if not project:
            return None
        manuscript = (
            self.workspace_service.get_manuscript(figure["manuscript_slug"]) or manifest.get_manuscript(figure["manuscript_slug"])
            if figure["manuscript_slug"]
            else None
        )
        return FigurePageContext(figure=figure, project=project, manuscript=manuscript)

    def tutorial_page(self) -> TutorialPageContext:
        manifest = self.repository.manifest()
        return TutorialPageContext(use_cases=manifest.use_cases)

    def docs_page(self, slug: str) -> DocsPageContext | None:
        if slug not in self.repository.doc_page_config:
            return None
        return DocsPageContext(
            selected_doc=self.repository.doc_page(slug),
            doc_pages=self.repository.doc_page_summaries(),
        )

    def use_case_page(self, slug: str) -> UseCasePageContext | None:
        manifest = self.repository.manifest()
        item = manifest.get_use_case(slug)
        if not item:
            return None
        previous_item, next_item = manifest.adjacent_use_cases(slug)
        return UseCasePageContext(item=item, previous_item=previous_item, next_item=next_item)
