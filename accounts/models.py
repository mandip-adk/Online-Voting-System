from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import random


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ('organizer', 'Organizer'),
        ('admin',     'Admin'),
    ]

    email             = models.EmailField(unique=True)
    first_name        = models.CharField(max_length=50)
    last_name         = models.CharField(max_length=50)
    role              = models.CharField(max_length=20, choices=ROLE_CHOICES, default='organizer')
    organization_name = models.CharField(max_length=200, blank=True)
    country           = models.CharField(max_length=100, blank=True)

    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.email} ({self.role})"


class PasswordResetOTP(models.Model):
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='password_reset_otps')
    otp        = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used    = models.BooleanField(default=False)

    def is_valid(self):
        """Returns True if OTP is not used and not expired."""
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_otp(cls):
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"OTP for {self.user.email} ({'valid' if self.is_valid() else 'expired/used'})"
    
    