from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('switch-role/', views.switch_role_view, name='switch_role'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('owner/kyc/', views.kyc_view, name='owner_kyc'),
    path('settings/', views.settings_view, name='settings'),
]

