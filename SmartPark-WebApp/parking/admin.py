from django.contrib import admin
from .models import ParkingLot, Slot


class SlotInline(admin.TabularInline):
    model = Slot
    extra = 0
    fields = ('slot_number', 'vehicle_type', 'row', 'column', 'status')


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'pincode', 'owner', 'car_price', 'bike_price', 'bus_price', 'status', 'is_accepting_bookings')
    list_filter = ('status', 'is_accepting_bookings', 'city')
    search_fields = ('name', 'city', 'pincode', 'address')
    inlines = [SlotInline]


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'parking_lot', 'vehicle_type', 'row', 'column', 'status')
    list_filter = ('vehicle_type', 'status', 'parking_lot')
    search_fields = ('slot_number', 'parking_lot__name')
