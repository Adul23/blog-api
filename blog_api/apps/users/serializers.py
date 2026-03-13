from rest_framework.serializers import (
    ModelSerializer,
    EmailField,
    CharField,
    BooleanField,
    ImageField,
    DateTimeField,
    ValidationError
    )
from .models import CustomUser, CustomManagerUser
import zoneinfo
class UserSerializer(ModelSerializer):
    
    password = CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', "first_name", "last_name"]
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user       

class LanguageUpdateSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['preferred_language']

class TimezoneUpdateSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['timezone']

    def validate_timezone(self, value):
        if value not in zoneinfo.available_timezones():
            # This covers the "All serializer validation errors are translatable" checkbox!
            raise ValidationError(_("Invalid IANA timezone identifier."))
        return value