from enum import StrEnum

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from enumfields import EnumField
from django.db import models


class UserType(StrEnum):
    CLIENT = "CLIENT",
    VISITOR = "VISITOR",
    ADMIN = "ADMIN"


class RegistrationStatus(StrEnum):
    APPROVED = "APPROVED",
    REJECTED = "REJECTED",
    PENDING = "PENDING"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    phone_number = models.TextField()
    email = models.EmailField(unique=True)
    user_type = EnumField(UserType, blank=True, null=True)
    company_name = models.TextField(max_length=200, blank=True)
    country_of_origin = models.TextField(max_length=100, blank=True)
    registration_status = EnumField(RegistrationStatus, default=RegistrationStatus.PENDING)
    # orcid_id = models.TextField(max_length=100)

    def get_absolute_url(self):
        return reverse("main:profile", kwargs={"pk": self.id})


class AdminComment(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)

    first_name = models.TextField(blank=True, default="")
    last_name = models.TextField(blank=True, default="")
    email = models.TextField(blank=True, default="")
    phone_number = models.TextField(blank=True, default="")
    company_name = models.TextField(blank=True, default="")
    country_of_origin = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
