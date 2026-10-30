from django.shortcuts import render
from parking.models import ParkingLot
from bookings.models import Booking


def welcome_view(request):
    total_locations = ParkingLot.objects.filter(status='active').count()
    total_bookings = Booking.objects.count()
    return render(request, 'welcome.html', {
        'total_locations': total_locations,
        'total_bookings': total_bookings,
    })
