"""
HuntIQ — Reports API Endpoint.

Endpoint for exporting multi-worksheet Excel workbooks (.xlsx).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_stub, get_db
from app.models.user import User
from app.reports.excel_generator import ExcelReportGeneratorService

router = APIRouter()


@router.get("/excel", response_class=Response)
async def export_excel_report(
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download executive job search performance report as Excel workbook (.xlsx)."""
    service = ExcelReportGeneratorService()
    excel_bytes = await service.generate_job_search_report(session, user.id)

    filename = f"HuntIQ_Report_{user.full_name.replace(' ', '_')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
