from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('host', 'Parking Host'),
    )

    KYC_STATUS_CHOICES = (
        ('not_submitted', 'Not Submitted'),
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True, null=True)
    aadhaar_no = models.CharField(max_length=20, blank=True, null=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='not_submitted')
    photo = models.ImageField(upload_to='kyc/photos/', blank=True, null=True)
    property_image = models.ImageField(upload_to='kyc/properties/', blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)

    def is_verified_host(self):
        return self.role == 'host' and self.kyc_status == 'verified'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
