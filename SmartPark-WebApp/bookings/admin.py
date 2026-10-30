from django.contrib import admin
from .models import Booking, Transaction


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_id',
        'customer_name',
        'parking_lot',
        'slot',
        'vehicle_type',
        'date',
        'price',
        'status',
        'payment_status',
        'created_at'
    )
    list_filter = ('status', 'payment_status', 'vehicle_type', 'payment_method', 'date')
    search_fields = ('booking_id', 'customer_name', 'customer_phone', 'vehicle_number', 'booking_email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'owner', 'amount', 'type', 'status', 'payment_method', 'created_at')
    list_filter = ('type', 'status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'owner__username', 'description')
