"""
Report listing and retrieval schemas.
"""

from typing import List, Optional, Any
from pydantic import BaseModel


class ReportSummary(BaseModel):
    id: str
    title: str
    type: str  # 'json' or 'markdown'
    description: str
    filename: str


class ReportDetail(BaseModel):
    id: str
    title: str
    type: str
    content: Any  # Dict for JSON, str for Markdown
