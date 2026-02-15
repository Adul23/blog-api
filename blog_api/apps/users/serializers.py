from rest_framework.serializers import (
    ModelSerializer,
    EmailField,
    CharField,
    BooleanField,
    ImageField,
    DateTimeField
    )
from .models import CustomUser, CustomManagerUser

class UserSerializer(ModelSerializer):
    
    password = CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', "first_name", "last_name"]
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user
