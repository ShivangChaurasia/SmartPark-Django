from django.conf import settings


def smartpark_context(request):
    """
    Context processor to inject global notification, role data, and map credentials into templates.
    """
    context = {
        'app_name': 'SmartPark',
        'maptiler_key': getattr(settings, 'MAPTILER_KEY', 'fJTNOS3Y93wHYjRBcSIY'),
        'recent_notifications': [],
        'has_notifications': False,
        'current_role': 'user',
        'is_verified_host': False,
    }

    if request.user.is_authenticated:
        context['current_role'] = request.user.role
        context['is_verified_host'] = request.user.is_verified_host()

        # Fetch recent bookings for the user's notification dropdown
        try:
            from bookings.models import Booking
            recent = Booking.objects.filter(
                user=request.user
            ).select_related('parking_lot', 'slot').order_by('-created_at')[:5]

            context['recent_notifications'] = recent
            context['has_notifications'] = recent.exists()
        except Exception:
            context['recent_notifications'] = []
            context['has_notifications'] = False

    return context
