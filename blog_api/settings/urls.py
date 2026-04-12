from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.users.views import RegisterViewSet, CustomRefreshViewSet, UpdateLanguageView, UpdateTimezoneView
from apps.blog.views import PostViewSet, CategoryViewSet, StatsView, sse_stream

router = DefaultRouter()
router.register(r'users', RegisterViewSet, basename='users')
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'categories', CategoryViewSet, basename='categories')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', CustomRefreshViewSet.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/register/', RegisterViewSet.as_view({'post': 'create'}), name='user-register'),
    path('api/users/login/', CustomRefreshViewSet.as_view(), name='user-login'),
    path('language/', UpdateLanguageView.as_view(), name='auth-language'),
    path('timezone/', UpdateTimezoneView.as_view(), name='auth-timezone'),

    # Schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Stats
    path('api/stats', StatsView.as_view(), name='stats'),

    # SSE — post publication stream (no auth required)
    path('api/posts/stream/', sse_stream, name='post-sse-stream'),

    # Notifications — polling endpoints
    path('api/notifications/', include('apps.notifications.urls')),
]
