"""Aggregate /api/v1 routes."""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    assets,
    assignments,
    attachments,
    auth,
    checklists,
    connectors_insights,
    customers,
    parts_used,
    portal,
    reports,
    schedule,
    service_locations,
    signoffs,
    time_entries,
    work_orders,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(
    service_locations.router, prefix="/service-locations", tags=["service-locations"]
)
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(work_orders.router, prefix="/work-orders", tags=["work-orders"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(checklists.router, prefix="/checklists", tags=["checklists"])
api_router.include_router(time_entries.router, prefix="/time-entries", tags=["time-entries"])
api_router.include_router(parts_used.router, prefix="/parts-used", tags=["parts-used"])
api_router.include_router(signoffs.router, tags=["signoffs"])
api_router.include_router(attachments.router, prefix="/attachments", tags=["attachments"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(portal.router, tags=["portal"])
api_router.include_router(connectors_insights.router)
