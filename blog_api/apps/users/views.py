from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import UserSerializer, LanguageUpdateSerializer, TimezoneUpdateSerializer
from .models import CustomUser


class UpdateLanguageView(UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = LanguageUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        tags=['Auth'],
        summary="Update User Language Preference",
        description=(
            "Updates the preferred language for the authenticated user."
        ),
        examples=[
            OpenApiExample('Valid Request', value={'preferred_language': 'ru'}, request_only=True),
            OpenApiExample('Success Response', value={'preferred_language': 'ru'}, response_only=True, status_codes=['200']),
        ],
        responses={200: LanguageUpdateSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class UpdateTimezoneView(UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = TimezoneUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterViewSet(GenericViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'refresh'

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        # Dispatch welcome email via Celery
        from apps.users.tasks import send_welcome_email
        send_welcome_email.delay(user.id)

        return Response({
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class CustomRefreshViewSet(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'refresh'
