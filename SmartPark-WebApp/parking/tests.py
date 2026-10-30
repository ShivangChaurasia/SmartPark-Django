from django.test import TestCase
from accounts.models import User
from parking.models import ParkingLot, Slot
from parking.views import calculate_haversine, generate_vehicle_slots


class ParkingLogicTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='lotowner',
            email='owner@example.com',
            password='password123',
            role='host',
            kyc_status='verified'
        )
        self.lot = ParkingLot.objects.create(
            owner=self.owner,
            name='Connaught Place Hub',
            address='Radial Road 1',
            city='New Delhi',
            pincode='110001',
            latitude=28.6315,
            longitude=77.2167,
            car_price=50.00,
            bike_price=20.00,
            bus_price=100.00,
            car_slots=5,
            bike_slots=6,
            bus_slots=2
        )

    def test_slot_generation(self):
        generate_vehicle_slots(self.lot, 5, 6, 2)
        self.assertEqual(self.lot.slots.filter(vehicle_type='car').count(), 5)
        self.assertEqual(self.lot.slots.filter(vehicle_type='bike').count(), 6)
        self.assertEqual(self.lot.slots.filter(vehicle_type='bus').count(), 2)
        self.assertEqual(self.lot.total_capacity(), 13)

    def test_haversine_distance(self):
        # Coordinates for New Delhi Connaught Place to India Gate (~2.3 km)
        dist = calculate_haversine(28.6315, 77.2167, 28.6129, 77.2295)
        self.assertAlmostEqual(dist, 2.4, delta=0.5)
