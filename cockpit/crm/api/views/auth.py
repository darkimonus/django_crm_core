from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenObtainPairView as _TokenObtainPairView,
    TokenRefreshView as _TokenRefreshView,
    TokenVerifyView as _TokenVerifyView,
)


@extend_schema(tags=["Auth"], summary="Obtain JWT access/refresh tokens")
class TokenObtainPairViewDoc(_TokenObtainPairView):
    pass


@extend_schema(tags=["Auth"], summary="Refresh JWT access token")
class TokenRefreshViewDoc(_TokenRefreshView):
    pass


@extend_schema(tags=["Auth"], summary="Verify JWT token validity")
class TokenVerifyViewDoc(_TokenVerifyView):
    pass
