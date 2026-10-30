from django import forms
from .models import ParkingLot


class ParkingLotForm(forms.ModelForm):
    class Meta:
        model = ParkingLot
        fields = [
            'name',
            'address',
            'city',
            'pincode',
            'latitude',
            'longitude',
            'car_price',
            'bike_price',
            'bus_price',
            'car_slots',
            'bike_slots',
            'bus_slots',
            'opening_time',
            'closing_time',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Facility / Parking Lot Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit PIN code'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Latitude (e.g. 28.6139)'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Longitude (e.g. 77.2090)'}),
            'car_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'bike_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'bus_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'car_slots': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '10'}),
            'bike_slots': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '10'}),
            'bus_slots': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '2'}),
            'opening_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '06:00'}),
            'closing_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '23:00'}),
        }

