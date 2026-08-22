from fastapi import APIRouter

from app.api import (
    admin,
    alerts,
    analytics,
    auth,
    companies,
    contacts,
    export,
    import_data,
    leads,
    projects,
    search,
    search_queries,
    settings,
    sources,
    tasks,
    tenders,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(tenders.router)
api_router.include_router(projects.router)
api_router.include_router(companies.router)
api_router.include_router(contacts.router)
api_router.include_router(sources.router)
api_router.include_router(search_queries.router)
api_router.include_router(search.router)
api_router.include_router(alerts.router)
api_router.include_router(tasks.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
api_router.include_router(admin.router)
api_router.include_router(export.router)
api_router.include_router(import_data.router)
