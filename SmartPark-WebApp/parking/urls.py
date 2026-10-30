from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_page, name='search'),
    path('api/search/', views.api_search, name='api_search'),
    path('parking/<int:pk>/', views.parking_detail, name='parking_detail'),
    path('api/parking-lots/<int:pk>/slots/', views.api_get_slots, name='api_get_slots'),

    # Owner / Host Routes
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/parking/<int:pk>/manage/', views.manage_lot, name='manage_lot'),
    path('api/owner/parking-lots/', views.api_store_parking_lot, name='api_store_parking_lot'),
    path('api/owner/parking-lots/<int:pk>/toggle-bookings/', views.api_toggle_bookings, name='api_toggle_bookings'),
    path('api/owner/parking-lots/<int:pk>/closure-summary/', views.api_get_closure_summary, name='api_get_closure_summary'),
    path('api/owner/parking-lots/<int:pk>/schedule-closure/', views.api_schedule_closure, name='api_schedule_closure'),
    path('api/owner/parking-lots/<int:pk>/cancel-closure/', views.api_cancel_closure, name='api_cancel_closure'),
    path('api/owner/manual-booking/', views.api_store_manual_booking, name='api_store_manual_booking'),
    path('api/owner/bookings/', views.api_owner_bookings, name='api_owner_bookings'),
    path('api/owner/verify-booking/', views.api_verify_booking, name='api_verify_booking'),
    path('api/owner/mark-attended/', views.api_mark_attended, name='api_mark_attended'),
]

