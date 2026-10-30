from django.db import models
from django.conf import settings


class ParkingLot(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('scheduled_for_removal', 'Scheduled for Removal'),
        ('inactive', 'Inactive'),
        ('permanently_removed', 'Permanently Removed'),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parking_lots')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    pincode = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    car_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    bike_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    bus_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)

    layout_type = models.CharField(max_length=50, default='dynamic')
    car_slots = models.PositiveIntegerField(default=0)
    bike_slots = models.PositiveIntegerField(default=0)
    bus_slots = models.PositiveIntegerField(default=0)

    opening_time = models.CharField(max_length=20, default='00:00')
    closing_time = models.CharField(max_length=20, default='23:59')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    is_accepting_bookings = models.BooleanField(default=True)
    removal_requested_at = models.DateTimeField(null=True, blank=True)
    scheduled_removal_date = models.DateField(null=True, blank=True)
    removal_reason = models.TextField(blank=True, null=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='removed_parking_lots'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_capacity(self):
        return self.car_slots + self.bike_slots + self.bus_slots

    def __str__(self):
        return f"{self.name} - {self.city} ({self.pincode})"


class Slot(models.Model):
    VEHICLE_TYPE_CHOICES = (
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('bus', 'Bus'),
    )

    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='slots')
    slot_number = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPE_CHOICES)
    row = models.PositiveIntegerField(default=1)
    column = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicle_type', 'row', 'column']

    def __str__(self):
        return f"{self.parking_lot.name} - Slot {self.slot_number} ({self.vehicle_type})"
