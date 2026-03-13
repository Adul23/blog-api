"""
URL configuration for blog_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from apps.users.views import RegisterViewSet, CustomRefreshViewSet, UpdateLanguageView, UpdateTimezoneView
from apps.blog.views import PostViewSet, CategoryViewSet, StatsView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


router = DefaultRouter()
router.register(r'users', RegisterViewSet, basename='users')
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'categories', CategoryViewSet, basename='categories')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', CustomRefreshViewSet.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/set-preferences/', UpdateUserPreferencesView.as_view(), name='set-preferences'),
    path('api/users/register/', RegisterViewSet.as_view({
                    'post': 'create'
                }), name='user-register'),
    path('api/users/login/', CustomRefreshViewSet.as_view(), name='user-login'),
    path('api/', include(router.urls)),
    path('language/', UpdateLanguageView.as_view(), name='auth-language'),
    path('timezone/', UpdateTimezoneView.as_view(), name='auth-timezone'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/stats', StatsView.as_view(), name='stats')
]