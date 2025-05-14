from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError('Enter a valid email address')
        
        # Check for required fields
        if not extra_fields.get('first_name'):
            raise ValueError('Users must have a first name')
        if not extra_fields.get('last_name'):
            raise ValueError('Users must have a last name')
        
        # Normalize email address
        email = self.normalize_email(email)
        
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False) 
    otp = models.IntegerField(null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def clean(self):
        """
        Add model-level validation
        """
        super().clean()
        validate_email(self.email)
    
    def user_image(self):
        """
        Returns the user's profile image if it exists
        """
        picture = UserImage.objects.filter(user=self).first()
        return picture.image if picture else None
    
    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """
        Returns the short name for the user (first name only).
        """
        return self.first_name
    
    def is_otp_expired(self):
        """Check if OTP is older than 1 hour"""
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + timedelta(hours=1)
        return True
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
class UserImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='user_images/')
    created_at = models.DateTimeField(default=timezone.now)
    