from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, customers, leads, opportunities, quotations, contracts, projects, dashboard, attachments, price_catalog, expenses, quotation_payments

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(customers.router)
api_router.include_router(leads.router)
api_router.include_router(opportunities.router)
api_router.include_router(quotations.router)
api_router.include_router(contracts.router)
api_router.include_router(projects.router)
api_router.include_router(projects.router_tasks)
api_router.include_router(attachments.router)
api_router.include_router(price_catalog.router)
api_router.include_router(expenses.router)
api_router.include_router(quotation_payments.router)
