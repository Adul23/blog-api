from django.db.models import (
    EmailField, CharField, BooleanField,
    DateTimeField, ImageField
)
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.password_validation import validate_password
from typing import Any
from django.core.exceptions import ValidationError

class CustomManagerUser(BaseUserManager):
    
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff=True.'))

        return self.create_user(email, password, **extra_fields)

        

# Create your models here.
class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    EMAIL_MAX_LENGTH = 150
    FULL_NAME_MAX_LENGTH = 150
    PASSWORD_MAX_LENGTH = 254

    email = EmailField(max_length=EMAIL_MAX_LENGTH, unique=True)
    first_name = CharField(max_length=FULL_NAME_MAX_LENGTH)
    last_name = CharField(max_length=FULL_NAME_MAX_LENGTH)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True)
    avatar = ImageField(upload_to='avatars/', null=True, blank=True)
    objects = CustomManagerUser()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        """Meta options for CustomUser model."""

        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"
        ordering = ["-date_joined"]
