from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('api/create-order/', views.api_create_order, name='api_create_order'),
    path('api/bookings/', views.api_create_booking, name='api_create_booking'),
    path('api/bookings/<int:pk>/cancel/', views.api_cancel_booking, name='api_cancel_booking'),
    path('api/bookings/<int:pk>/extend/', views.api_extend_booking, name='api_extend_booking'),
    path('invoice/<int:pk>/download/', views.download_ticket, name='invoice_download'),
    path('invoice/<int:pk>/view/', views.view_ticket, name='invoice_view'),
]

