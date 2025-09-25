# Routes package
from .auth import router as auth_router
from .clients import router as clients_router
from .services import router as services_router
from .appointments import router as appointments_router
from .reports import router as reports_router
from .professionals import router as professionals_router
from .business_hours import router as business_hours_router
from .salons import router as salons_router
from .monitoring import router as monitoring_router

__all__ = ["auth_router", "clients_router", "services_router", "appointments_router", "reports_router", "professionals_router", "business_hours_router", "salons_router", "monitoring_router"]