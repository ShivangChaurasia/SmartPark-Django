from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from parking.models import ParkingLot, Slot
from parking.views import generate_vehicle_slots
from bookings.models import Booking, Transaction


class Command(BaseCommand):
    help = 'Seeds initial demonstration data for SmartPark Django platform.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding SmartPark demo dataset...")

        # 1. Superuser / Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartpark.com',
                'is_staff': True,
                'is_superuser': True,
                'role': 'host',
                'kyc_status': 'verified',
                'onboarding_completed': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write("Created Superuser: admin (password: admin123)")

        # 2. Demo Host
        host, created = User.objects.get_or_create(
            username='host_demo',
            defaults={
                'email': 'host@smartpark.com',
                'first_name': 'Ramesh',
                'last_name': 'Verma',
                'role': 'host',
                'phone': '9876543210',
                'aadhaar_no': '123456789012',
                'kyc_status': 'verified',
                'onboarding_completed': True
            }
        )
        if created:
            host.set_password('host123')
            host.save()
            self.stdout.write("Created Host: host_demo (password: host123)")

        # 3. Demo Driver User
        driver, created = User.objects.get_or_create(
            username='driver_demo',
            defaults={
                'email': 'driver@smartpark.com',
                'first_name': 'Ankit',
                'last_name': 'Sharma',
                'role': 'user',
                'phone': '9123456789',
                'onboarding_completed': True
            }
        )
        if created:
            driver.set_password('driver123')
            driver.save()
            self.stdout.write("Created Driver: driver_demo (password: driver123)")

        # 4. Parking Facilities
        lot1, _ = ParkingLot.objects.get_or_create(
            name='Connaught Place Smart Parking',
            defaults={
                'owner': host,
                'address': 'Radial Road 2, Inner Circle',
                'city': 'New Delhi',
                'pincode': '110001',
                'latitude': 28.6315,
                'longitude': 77.2167,
                'car_price': 50.00,
                'bike_price': 20.00,
                'bus_price': 100.00,
                'car_slots': 15,
                'bike_slots': 10,
                'bus_slots': 2,
                'opening_time': '06:00',
                'closing_time': '23:30',
                'status': 'active',
                'is_accepting_bookings': True
            }
        )
        if lot1.slots.count() == 0:
            generate_vehicle_slots(lot1, lot1.car_slots, lot1.bike_slots, lot1.bus_slots)
            self.stdout.write(f"Generated slots for {lot1.name}")

        lot2, _ = ParkingLot.objects.get_or_create(
            name='Cyber City Express Hub',
            defaults={
                'owner': host,
                'address': 'DLF Phase 2, Sector 24',
                'city': 'Gurgaon',
                'pincode': '122002',
                'latitude': 28.4900,
                'longitude': 77.0900,
                'car_price': 60.00,
                'bike_price': 25.00,
                'bus_price': 120.00,
                'car_slots': 12,
                'bike_slots': 8,
                'bus_slots': 2,
                'opening_time': '00:00',
                'closing_time': '23:59',
                'status': 'active',
                'is_accepting_bookings': True
            }
        )
        if lot2.slots.count() == 0:
            generate_vehicle_slots(lot2, lot2.car_slots, lot2.bike_slots, lot2.bus_slots)
            self.stdout.write(f"Generated slots for {lot2.name}")

        lot3, _ = ParkingLot.objects.get_or_create(
            name='Indiranagar Mobility Deck',
            defaults={
                'owner': host,
                'address': '100 Feet Road, HAL 2nd Stage',
                'city': 'Bengaluru',
                'pincode': '560038',
                'latitude': 12.9716,
                'longitude': 77.6412,
                'car_price': 40.00,
                'bike_price': 15.00,
                'bus_price': 80.00,
                'car_slots': 10,
                'bike_slots': 6,
                'bus_slots': 0,
                'opening_time': '07:00',
                'closing_time': '23:00',
                'status': 'active',
                'is_accepting_bookings': True
            }
        )
        if lot3.slots.count() == 0:
            generate_vehicle_slots(lot3, lot3.car_slots, lot3.bike_slots, lot3.bus_slots)
            self.stdout.write(f"Generated slots for {lot3.name}")

        lot4, _ = ParkingLot.objects.get_or_create(
            name='Administration Block Parking',
            defaults={
                'owner': host,
                'address': 'Lovely Professional University, GT Road',
                'city': 'Phagwara',
                'pincode': '144411',
                'latitude': 31.2536,
                'longitude': 75.7037,
                'car_price': 30.00,
                'bike_price': 10.00,
                'bus_price': 50.00,
                'car_slots': 50,
                'bike_slots': 30,
                'bus_slots': 5,
                'opening_time': '06:00',
                'closing_time': '22:00',
                'status': 'active',
                'is_accepting_bookings': True
            }
        )
        if lot4.slots.count() == 0:
            generate_vehicle_slots(lot4, lot4.car_slots, lot4.bike_slots, lot4.bus_slots)
            self.stdout.write(f"Generated slots for {lot4.name}")

        lot5, _ = ParkingLot.objects.get_or_create(
            name='Himanshu Shekhar Plaza',
            defaults={
                'owner': host,
                'address': 'Ramandai, Near Bus Stand',
                'city': 'Jalandhar',
                'pincode': '144001',
                'latitude': 31.3260,
                'longitude': 75.5762,
                'car_price': 20.00,
                'bike_price': 10.00,
                'bus_price': 40.00,
                'car_slots': 20,
                'bike_slots': 15,
                'bus_slots': 0,
                'opening_time': '07:00',
                'closing_time': '23:00',
                'status': 'active',
                'is_accepting_bookings': True
            }
        )
        if lot5.slots.count() == 0:
            generate_vehicle_slots(lot5, lot5.car_slots, lot5.bike_slots, lot5.bus_slots)
            self.stdout.write(f"Generated slots for {lot5.name}")

        # 5. Seed sample bookings for driver_demo
        slot_sample = lot1.slots.filter(vehicle_type='car').first()
        now = timezone.now()

        # Active session
        b_active, created = Booking.objects.get_or_create(
            booking_id='PKLIVE1001',
            defaults={
                'user': driver,
                'customer_name': 'Ankit Sharma',
                'customer_phone': '9123456789',
                'vehicle_number': 'DL01AB9988',
                'parking_lot': lot1,
                'slot': slot_sample,
                'vehicle_type': 'car',
                'booking_start_datetime': now - timedelta(minutes=25),
                'booking_end_datetime': now + timedelta(minutes=65),
                'booking_duration_minutes': 90,
                'date': now.date(),
                'time_slot_id': f"{(now - timedelta(minutes=25)).strftime('%H:%M')}-{(now + timedelta(minutes=65)).strftime('%H:%M')}",
                'price': 75.00,
                'status': 'active',
                'payment_status': 'paid',
                'payment_method': 'razorpay'
            }
        )
        if created:
            Transaction.objects.create(
                user=driver,
                owner=host,
                booking=b_active,
                amount=75.00,
                type='payment',
                status='completed',
                payment_method='razorpay',
                description=f"Reservation for slot {slot_sample.slot_number} at {lot1.name}"
            )
            Transaction.objects.create(
                user=driver,
                owner=host,
                booking=b_active,
                amount=75.00,
                type='earning',
                status='completed',
                payment_method='razorpay',
                description=f"Host earning for slot {slot_sample.slot_number} at {lot1.name}"
            )

        # Upcoming session tomorrow
        slot_sample2 = lot1.slots.filter(vehicle_type='car').last()
        tomorrow_start = (now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(hours=2)

        b_upcoming, created = Booking.objects.get_or_create(
            booking_id='PKUPCM2002',
            defaults={
                'user': driver,
                'customer_name': 'Ankit Sharma',
                'customer_phone': '9123456789',
                'vehicle_number': 'DL01AB9988',
                'parking_lot': lot1,
                'slot': slot_sample2,
                'vehicle_type': 'car',
                'booking_start_datetime': tomorrow_start,
                'booking_end_datetime': tomorrow_end,
                'booking_duration_minutes': 120,
                'date': tomorrow_start.date(),
                'time_slot_id': '14:00-16:00',
                'price': 100.00,
                'status': 'upcoming',
                'payment_status': 'paid',
                'payment_method': 'razorpay'
            }
        )
        if created:
            Transaction.objects.create(
                user=driver,
                owner=host,
                booking=b_upcoming,
                amount=100.00,
                type='payment',
                status='completed',
                payment_method='razorpay',
                description=f"Reservation for slot {slot_sample2.slot_number} at {lot1.name}"
            )
            Transaction.objects.create(
                user=driver,
                owner=host,
                booking=b_upcoming,
                amount=100.00,
                type='earning',
                status='completed',
                payment_method='razorpay',
                description=f"Host earning for slot {slot_sample2.slot_number} at {lot1.name}"
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded SmartPark Django demo database!"))

