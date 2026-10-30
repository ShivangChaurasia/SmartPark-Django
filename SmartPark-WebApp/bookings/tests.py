from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from parking.models import ParkingLot, Slot
from bookings.models import Booking
from bookings.ticket_generator import generate_ticket_pdf


class BookingEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='driver1', email='driver@example.com', password='password123')
        self.owner = User.objects.create_user(username='host1', email='host@example.com', password='password123', role='host', kyc_status='verified')
        self.lot = ParkingLot.objects.create(
            owner=self.owner,
            name='Central Station Lot',
            address='Station Road',
            city='Delhi',
            pincode='110006',
            latitude=28.6500,
            longitude=77.2200,
            car_price=40.00
        )
        self.slot = Slot.objects.create(
            parking_lot=self.lot,
            slot_number='C-101',
            vehicle_type='car'
        )

    def test_overlap_collision_detection(self):
        base_time = timezone.now() + timedelta(days=1)
        booking1_start = base_time.replace(hour=10, minute=0, second=0, microsecond=0)
        booking1_end = base_time.replace(hour=12, minute=0, second=0, microsecond=0)

        # Create initial booking
        Booking.objects.create(
            booking_id='BKTEST0001',
            user=self.user,
            parking_lot=self.lot,
            slot=self.slot,
            vehicle_type='car',
            booking_start_datetime=booking1_start,
            booking_end_datetime=booking1_end,
            booking_duration_minutes=120,
            date=booking1_start.date(),
            price=80.00,
            status='confirmed',
            payment_status='paid'
        )

        # Attempt overlapping booking: 11:00 to 13:00 (overlaps from 11:00 to 12:00)
        test_start = base_time.replace(hour=11, minute=0, second=0, microsecond=0)
        test_end = base_time.replace(hour=13, minute=0, second=0, microsecond=0)

        is_colliding = Booking.objects.filter(
            parking_lot=self.lot,
            slot=self.slot,
            status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
            booking_start_datetime__lt=test_end,
            booking_end_datetime__gt=test_start
        ).exists()

        self.assertTrue(is_colliding, "Overlapping booking window must be detected as collision.")

        # Attempt non-overlapping consecutive booking: 12:00 to 14:00 (starts when previous ends)
        consec_start = base_time.replace(hour=12, minute=0, second=0, microsecond=0)
        consec_end = base_time.replace(hour=14, minute=0, second=0, microsecond=0)

        is_consec_colliding = Booking.objects.filter(
            parking_lot=self.lot,
            slot=self.slot,
            status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
            booking_start_datetime__lt=consec_end,
            booking_end_datetime__gt=consec_start
        ).exists()

        self.assertFalse(is_consec_colliding, "Consecutive booking starting exactly when previous ends should be valid.")

    def test_pdf_ticket_generation(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1)
        booking = Booking.objects.create(
            booking_id='BKTICKET01',
            user=self.user,
            customer_name='John Tester',
            customer_phone='9876543210',
            vehicle_number='DL01XY9999',
            parking_lot=self.lot,
            slot=self.slot,
            vehicle_type='car',
            booking_start_datetime=start,
            booking_end_datetime=end,
            booking_duration_minutes=60,
            date=start.date(),
            time_slot_id='10:00-11:00',
            price=40.00,
            status='upcoming',
            payment_status='paid'
        )

        pdf_content = generate_ticket_pdf(booking)
        self.assertIsNotNone(pdf_content)
        self.assertTrue(len(pdf_content) > 1000, "Generated PDF must contain valid binary ticket data.")
        self.assertTrue(pdf_content.startswith(b'%PDF'), "PDF content must start with PDF header bytes.")
