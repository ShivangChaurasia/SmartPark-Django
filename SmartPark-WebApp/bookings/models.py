from django.db import models
from django.conf import settings
from parking.models import ParkingLot, Slot


class Booking(models.Model):
    STATUS_CHOICES = (
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending_verification', 'Pending Verification'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('razorpay', 'Razorpay'),
        ('manual_qr', 'Manual QR / Cash'),
    )

    booking_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='bookings')
    booking_email = models.EmailField(blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    vehicle_number = models.CharField(max_length=30, blank=True, null=True)

    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='bookings')
    vehicle_type = models.CharField(max_length=20)

    booking_start_datetime = models.DateTimeField()
    booking_end_datetime = models.DateTimeField()
    booking_duration_minutes = models.PositiveIntegerField(default=60)
    date = models.DateField()
    time_slot_id = models.CharField(max_length=50, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='paid')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='razorpay')

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    invoice_path = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)

    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    refund_status = models.CharField(max_length=50, default='none')
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # No-show penalty: set when a manual_qr booking expires without attendance/cancellation.
    # The penalty (= 100% of booking price) is added to the user's next manual_qr booking total.
    no_show_penalty = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    penalty_applied = models.BooleanField(default=False)  # True once penalty has been collected on the next booking

    attended_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_bookings'
    )
    extended_from_booking_id = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_start_datetime']

    def __str__(self):
        return f"Booking #{self.booking_id} - {self.parking_lot.name} Slot {self.slot.slot_number}"


class Transaction(models.Model):
    TYPE_CHOICES = (
        ('payment', 'Payment'),
        ('earning', 'Earning'),
        ('refund', 'Refund'),
    )

    STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='owner_transactions')
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.CASCADE, related_name='transactions')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    payment_method = models.CharField(max_length=50, default='razorpay')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.type} - ₹{self.amount} ({self.status})"
