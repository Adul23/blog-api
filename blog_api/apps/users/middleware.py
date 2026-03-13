from django.utils import translation
from django.conf import settings
from django.utils import timezone
import zoneinfo

class CustomLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = None
        user = getattr(request, 'user', None)

        if user and user.is_authenticated:
            if getattr(user, 'preferred_language', None):
                language = user.preferred_language
            
            if getattr(user, 'timezone', None):
                try:
                    tzname = zoneinfo.ZoneInfo(user.timezone)
                    timezone.activate(tzname)
                except zoneinfo.ZoneInfoNotFoundError:
                    pass

        if not language:
            lang_param = request.GET.get('lang')
            if lang_param and lang_param in dict(settings.LANGUAGES).keys():
                language = lang_param

        if not language:
            language = translation.get_language_from_request(request)

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

        response = self.get_response(request)

        translation.deactivate()
        timezone.deactivate()
        
        return response