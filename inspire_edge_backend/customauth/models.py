from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import pyotp


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    TIER_CHOICES = (
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    )
    username = None
    email = models.EmailField(_('email address'), unique=True)


    is_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    business_name = models.CharField(max_length=100, blank=True, null=True)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='basic')
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    trial_used = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)  # True if user has upgraded/purchased
    subscription_end = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def roles(self):
        return self.userrole_set.select_related('role').values_list('role__name', flat=True)

    def start_trial(self):
        if not self.trial_used:
            self.tier = 'pro'
            self.trial_start = timezone.now()
            self.trial_end = timezone.now() + timedelta(days=14)
            self.trial_used = True
            self.save()

    def activate_paid_subscription(self, months=1, tier='pro'):
        self.tier = tier
        self.is_paid = True
        if self.subscription_end and self.subscription_end > timezone.now():
            self.subscription_end += timedelta(days=30 * months)
        else:
            self.subscription_end = timezone.now() + timedelta(days=30 * months)
        self.save()

    def downgrade_if_expired(self):
        now = timezone.now()
        if self.trial_end and not self.is_paid and self.trial_end <= now:
            self.tier = 'basic'
            self.save()
        elif self.subscription_end and self.subscription_end <= now:
            self.tier = 'basic'
            self.is_paid = False
            self.save()

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'role')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
        ]
    def __str__(self):
        return f"{self.user.email} → {self.role.name}"

class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_secret = models.CharField(max_length=32)
    otp_verified = models.BooleanField(default=False)
    created = models.DateTimeField(default=timezone.now)
    def generate_otp(self):
        self.otp_verified = False
        self.created = timezone.now()
        self.save()
        totp = pyotp.TOTP(self.otp_secret, interval=300)
        return totp.now()
    def verify_otp(self, otp_code):
        totp = pyotp.TOTP(self.otp_secret)
        if totp.verify(otp_code):
            self.otp_verified = True
            self.save()
            return True
        return False
    def __str__(self):

        return f"OTP for {self.user.email}"

class PaymentType(models.Model):
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=User.TIER_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField()


