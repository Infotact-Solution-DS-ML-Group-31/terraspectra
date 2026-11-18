"""
Scientific reports catalog and retrieval endpoints.
"""

from typing import List
from fastapi import APIRouter, HTTPException

from backend.app.schemas.report import ReportSummary, ReportDetail
from backend.app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Scientific Reports"])


@router.get("", response_model=List[ReportSummary])
def list_reports():
    """List all available scientific analysis reports (JSON summaries and Markdown documentation)."""
    return report_service.list_reports()


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: str):
    """Retrieve the content of a specific scientific report by ID."""
    report = report_service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' was not found."
        )
    return report
