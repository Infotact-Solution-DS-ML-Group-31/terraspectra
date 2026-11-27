"""
Service for cataloging and retrieving Phase B & C scientific reports.
"""

from typing import List, Optional, Dict, Any
import json

from backend.app.config import REPORTS_DIR, DOCS_DIR
from backend.app.schemas.report import ReportSummary, ReportDetail


REPORTS_CATALOG = [
    {
        "id": "dataset_inventory",
        "title": "Dataset Inventory (904 Records)",
        "type": "json",
        "description": "Comprehensive metadata audit, cube scarcity, and missing files breakdown.",
        "path": REPORTS_DIR / "dataset_inventory.json"
    },
    {
        "id": "biological_sample_summary",
        "title": "Biological Sample Structure (49 Plants)",
        "type": "json",
        "description": "Plant identity grouping, repeated observation distributions, and confounder analysis.",
        "path": REPORTS_DIR / "biological_sample_summary.json"
    },
    {
        "id": "ml_feasibility_summary",
        "title": "Machine Learning Feasibility & Leakage Audit",
        "type": "json",
        "description": "Audit of 5 ML tasks and simulation showing 100% data leakage in naive random splits.",
        "path": REPORTS_DIR / "ml_feasibility_summary.json"
    },
    {
        "id": "3079_spectral_robustness_summary",
        "title": "Spectral Robustness Analysis (Image 3079)",
        "type": "json",
        "description": "ROI boundary erosion sensitivity, 16x16 spatial blocks, and band stability results.",
        "path": REPORTS_DIR / "3079_spectral_robustness_summary.json"
    },
    {
        "id": "3079_lesion_level_spectral_summary",
        "title": "Three-Region Spectral Profile (Image 3079)",
        "type": "json",
        "description": "Per-band statistics and pairwise spectral divergence for Lesion vs Unaffected vs Comparison stem.",
        "path": REPORTS_DIR / "3079_lesion_level_spectral_summary.json"
    },
    {
        "id": "dataset_suitability_assessment",
        "title": "Dataset Suitability & Feasibility Report",
        "type": "markdown",
        "description": "Full 11-section markdown document assessing biological structure and ML feasibility.",
        "path": DOCS_DIR / "dataset_suitability_assessment.md"
    },
    {
        "id": "3079_spectral_robustness_report",
        "title": "Spectral Robustness Experiment Report",
        "type": "markdown",
        "description": "Full scientific markdown report on morphological erosion and spatial block aggregation.",
        "path": DOCS_DIR / "3079_spectral_robustness_report.md"
    },
    {
        "id": "phase_f3_unsupervised_clustering",
        "title": "Phase F3 Unsupervised Clustering Results (JSON)",
        "type": "json",
        "description": "Experiment configuration, K=2..5 silhouette, stability ARI, and post-hoc ROI comparison.",
        "path": REPORTS_DIR / "phase_f3_unsupervised_clustering.json"
    },
    {
        "id": "phase_f3_unsupervised_clustering_report",
        "title": "Phase F3 Unsupervised Spectral Learning Report",
        "type": "markdown",
        "description": "Methodology, per-cube results, stability findings, and scientific limitations for Phase F3.",
        "path": DOCS_DIR / "phase_f3_unsupervised_clustering.md"
    }
]


class ReportService:
    def list_reports(self) -> List[ReportSummary]:
        results = []
        for r in REPORTS_CATALOG:
            if r["path"].exists():
                results.append(ReportSummary(
                    id=r["id"],
                    title=r["title"],
                    type=r["type"],
                    description=r["description"],
                    filename=r["path"].name
                ))
        return results

    def get_report(self, report_id: str) -> Optional[ReportDetail]:
        entry = next((r for r in REPORTS_CATALOG if r["id"] == report_id), None)
        if not entry or not entry["path"].exists():
            return None

        if entry["type"] == "json":
            with open(entry["path"], "r", encoding="utf-8") as f:
                content = json.load(f)
        else:
            with open(entry["path"], "r", encoding="utf-8") as f:
                content = f.read()

        return ReportDetail(
            id=entry["id"],
            title=entry["title"],
            type=entry["type"],
            content=content
        )


report_service = ReportService()
