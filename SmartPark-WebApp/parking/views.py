import json
import math
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Sum
from django.contrib import messages
from .models import ParkingLot, Slot
from bookings.models import Booking, Transaction


def calculate_haversine(lat1, lon1, lat2, lon2):
    """
    Haversine algorithm to calculate geographical distance in km between two GPS coordinates.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_vehicle_slots(lot, car_count, bike_count, bus_count):
    """
    Generates structured slots with layout grid positions for cars, bikes, and buses.
    """
    slots_to_create = []

    # Cars (C-101, C-102...)
    for i in range(1, car_count + 1):
        row = ((i - 1) // 5) + 1
        col = ((i - 1) % 5) + 1
        slots_to_create.append(Slot(
            parking_lot=lot,
            slot_number=f"C-{100 + i}",
            vehicle_type='car',
            row=row,
            column=col
        ))

    # Bikes (B-101, B-102...)
    for i in range(1, bike_count + 1):
        row = ((i - 1) // 6) + 1
        col = ((i - 1) % 6) + 1
        slots_to_create.append(Slot(
            parking_lot=lot,
            slot_number=f"B-{100 + i}",
            vehicle_type='bike',
            row=row,
            column=col
        ))

    # Buses (BUS-101...)
    for i in range(1, bus_count + 1):
        slots_to_create.append(Slot(
            parking_lot=lot,
            slot_number=f"BUS-{100 + i}",
            vehicle_type='bus',
            row=1,
            column=i
        ))

    Slot.objects.bulk_create(slots_to_create)


def search_page(request):
    return render(request, 'parking/search.html')


def api_search(request):
    """
    Discovers nearby parking spots filtered by GPS coordinates (Haversine 10km) or PIN code.
    """
    query = ParkingLot.objects.exclude(status__in=['inactive', 'permanently_removed'])
    query = query.filter(Q(is_accepting_bookings=True))

    selected_date = request.GET.get('date')
    if selected_date:
        query = query.filter(
            Q(scheduled_removal_date__isnull=True) | Q(scheduled_removal_date__gte=selected_date)
        )

    pincode = request.GET.get('pincode')
    if pincode:
        query = query.filter(pincode=pincode.strip())

    lots = list(query)
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    results = []
    for lot in lots:
        distance = None
        if lat and lng:
            try:
                user_lat = float(lat)
                user_lng = float(lng)
                distance = calculate_haversine(user_lat, user_lng, lot.latitude, lot.longitude)
                if distance > 15:  # within 15 km radius
                    continue
            except (ValueError, TypeError):
                pass

        results.append({
            'id': lot.id,
            '_id': str(lot.id),
            'name': lot.name,
            'address': lot.address,
            'city': lot.city,
            'pincode': lot.pincode,
            'latitude': lot.latitude,
            'longitude': lot.longitude,
            'car_price': float(lot.car_price),
            'bike_price': float(lot.bike_price),
            'bus_price': float(lot.bus_price),
            'car_slots': lot.car_slots,
            'bike_slots': lot.bike_slots,
            'bus_slots': lot.bus_slots,
            'distance': round(distance, 2) if distance is not None else None,
            'status': lot.status,
            'is_accepting_bookings': lot.is_accepting_bookings,
        })

    # Sort by distance if coordinates provided
    if lat and lng:
        results.sort(key=lambda x: (x['distance'] is None, x['distance']))

    return JsonResponse({'data': results})


@login_required
def parking_detail(request, pk):
    lot = get_object_or_404(ParkingLot, pk=pk)
    return render(request, 'parking/detail.html', {'lot': lot, 'id': lot.id})


def api_get_slots(request, pk):
    """
    Returns real-time slots and calculates occupied state based on requested time range.
    Overlap condition: (booking_start < requested_end) AND (booking_end > requested_start)
    """
    start_str = request.GET.get('start_datetime')
    end_str = request.GET.get('end_datetime')

    if not start_str or not end_str:
        return JsonResponse({'slots': []})

    try:
        requested_start = timezone.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        requested_end = timezone.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    except Exception:
        return JsonResponse({'slots': []})

    if timezone.is_naive(requested_start):
        requested_start = timezone.make_aware(requested_start, timezone.get_current_timezone())
    if timezone.is_naive(requested_end):
        requested_end = timezone.make_aware(requested_end, timezone.get_current_timezone())

    lot = get_object_or_404(ParkingLot, pk=pk)
    if lot.status in ['inactive', 'permanently_removed'] or not lot.is_accepting_bookings:
        return JsonResponse({'slots': []})

    all_slots = lot.slots.all()

    # Double-booking prevention query
    booked_slot_ids = set(Booking.objects.filter(
        parking_lot=lot,
        status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
        booking_start_datetime__lt=requested_end,
        booking_end_datetime__gt=requested_start
    ).values_list('slot_id', flat=True))

    slots_data = []
    for slot in all_slots:
        slots_data.append({
            'id': slot.id,
            '_id': str(slot.id),
            'slot_number': slot.slot_number,
            'vehicle_type': slot.vehicle_type,
            'row': slot.row,
            'column': slot.column,
            'is_booked': slot.id in booked_slot_ids,
        })

    return JsonResponse({'slots': slots_data})


@login_required
def owner_dashboard(request):
    user = request.user
    if user.kyc_status != 'verified':
        messages.warning(request, "Host KYC verification required to access Owner Dashboard.")
        return redirect('owner_kyc')

    lots = ParkingLot.objects.filter(owner=user)
    lot_ids = lots.values_list('id', flat=True)

    total_lots = lots.count()
    total_slots = Slot.objects.filter(parking_lot__in=lot_ids).count()
    active_bookings_count = Booking.objects.filter(
        parking_lot__in=lot_ids,
        status__in=['confirmed', 'upcoming', 'active', 'attended'],
        date__gte=timezone.now().date()
    ).count()

    transactions = Transaction.objects.filter(owner=user).select_related('booking')
    total_earnings = transactions.filter(status='completed', type='earning').aggregate(total=Sum('amount'))['total'] or 0

    # Revenue Breakdown for Chart.js (Past 7 days)
    today = timezone.now().date()
    revenue_chart_labels = []
    revenue_chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime('%d %b')
        revenue_chart_labels.append(day_str)
        day_earning = transactions.filter(
            status='completed',
            type='earning',
            created_at__date=day
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_chart_data.append(float(day_earning))

    context = {
        'parkingLots': lots,
        'totalParkingLots': total_lots,
        'totalSlots': total_slots,
        'activeBookingsCount': active_bookings_count,
        'transactions': transactions[:15],
        'totalEarnings': total_earnings,
        'revenue_labels_json': json.dumps(revenue_chart_labels),
        'revenue_data_json': json.dumps(revenue_chart_data),
    }

    return render(request, 'parking/owner_dashboard.html', context)


@login_required
def manage_lot(request, pk):
    lot = get_object_or_404(ParkingLot, pk=pk, owner=request.user)
    return render(request, 'parking/manage.html', {'parkingLot': lot})


@login_required
@require_POST
def api_store_parking_lot(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        lot = ParkingLot.objects.create(
            owner=request.user,
            name=data.get('name'),
            address=data.get('address'),
            pincode=data.get('pincode'),
            city=data.get('city'),
            latitude=float(data.get('latitude', 0.0)),
            longitude=float(data.get('longitude', 0.0)),
            car_price=float(data.get('car_price', 0.0)),
            bike_price=float(data.get('bike_price', 0.0)),
            bus_price=float(data.get('bus_price', 0.0)),
            car_slots=int(data.get('car_slots', 10)),
            bike_slots=int(data.get('bike_slots', 10)),
            bus_slots=int(data.get('bus_slots', 2)),
            opening_time=data.get('opening_time', '06:00'),
            closing_time=data.get('closing_time', '23:00'),
        )

        generate_vehicle_slots(lot, lot.car_slots, lot.bike_slots, lot.bus_slots)

        return JsonResponse({
            'message': 'Parking lot created successfully',
            'parking_lot': {'id': lot.id, 'name': lot.name}
        }, status=201)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@login_required
@require_POST
def api_toggle_bookings(request, pk):
    lot = get_object_or_404(ParkingLot, pk=pk, owner=request.user)
    if lot.status in ['inactive', 'permanently_removed']:
        return JsonResponse({'message': 'Cannot toggle bookings for inactive parking lots.'}, status=400)

    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        is_accepting = data.get('is_accepting_bookings')
        if isinstance(is_accepting, str):
            is_accepting = is_accepting.lower() in ['true', '1']
        lot.is_accepting_bookings = bool(is_accepting)
        lot.save()

        return JsonResponse({
            'message': 'Booking status updated successfully.',
            'is_accepting_bookings': lot.is_accepting_bookings
        })
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@login_required
def api_get_closure_summary(request, pk):
    lot = get_object_or_404(ParkingLot, pk=pk, owner=request.user)
    active_bookings = Booking.objects.filter(
        parking_lot=lot,
        status__in=['confirmed', 'pending', 'upcoming', 'active']
    )

    latest_booking = active_bookings.order_by('-date').first()
    min_date = timezone.now().date() + timedelta(days=7)
    closure_date = min_date

    if latest_booking and latest_booking.date >= min_date:
        closure_date = latest_booking.date + timedelta(days=1)

    revenue_impact = active_bookings.aggregate(total=Sum('price'))['total'] or 0

    return JsonResponse({
        'scheduled_removal_date': closure_date.strftime('%Y-%m-%d'),
        'active_bookings_count': active_bookings.count(),
        'latest_booking_date': latest_booking.date.strftime('%Y-%m-%d') if latest_booking else None,
        'revenue_impact': float(revenue_impact),
    })


@login_required
@require_POST
def api_schedule_closure(request, pk):
    lot = get_object_or_404(ParkingLot, pk=pk, owner=request.user)
    if lot.status in ['scheduled_for_removal', 'inactive', 'permanently_removed']:
        return JsonResponse({'message': 'Parking lot is already scheduled for closure or inactive.'}, status=400)

    summary_res = api_get_closure_summary(request, pk)
    data = json.loads(summary_res.content)

    post_data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

    lot.status = 'scheduled_for_removal'
    lot.removal_requested_at = timezone.now()
    lot.scheduled_removal_date = data['scheduled_removal_date']
    lot.removal_reason = post_data.get('reason', '')
    lot.removed_by = request.user
    lot.save()

    return JsonResponse({
        'message': 'Closure scheduled successfully.',
        'scheduled_removal_date': lot.scheduled_removal_date.strftime('%Y-%m-%d'),
        'active_bookings_count': data['active_bookings_count']
    })


@login_required
@require_POST
def api_cancel_closure(request, pk):
    lot = get_object_or_404(ParkingLot, pk=pk, owner=request.user)
    lot.status = 'active'
    lot.scheduled_removal_date = None
    lot.removal_requested_at = None
    lot.removal_reason = None
    lot.removed_by = None
    lot.is_accepting_bookings = True
    lot.save()

    return JsonResponse({
        'message': 'Scheduled closure has been cancelled. Parking lot is now active.',
        'status': lot.status
    })


@login_required
@require_POST
def api_store_manual_booking(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        lot_id = data.get('parking_lot_id')
        slot_ids = data.get('slot_ids', [])
        if isinstance(slot_ids, str):
            slot_ids = [slot_ids]

        start_str = data.get('start_datetime')
        end_str = data.get('end_datetime')

        start = timezone.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end = timezone.datetime.fromisoformat(end_str.replace('Z', '+00:00'))

        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())

        lot = get_object_or_404(ParkingLot, pk=lot_id, owner=request.user)
        duration_minutes = int((end - start).total_seconds() // 60)

        import random, string
        created_bookings = []

        for sid in slot_ids:
            slot = get_object_or_404(Slot, pk=sid, parking_lot=lot)

            # Check overlap
            exists = Booking.objects.filter(
                slot=slot,
                status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
                booking_start_datetime__lt=end,
                booking_end_datetime__gt=start
            ).exists()

            if exists:
                return JsonResponse({'message': f"Slot {slot.slot_number} is already booked for this duration."}, status=409)

            hourly = lot.car_price if slot.vehicle_type == 'car' else (lot.bike_price if slot.vehicle_type == 'bike' else lot.bus_price)
            price = (duration_minutes / 60) * float(hourly)

            b_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            booking = Booking.objects.create(
                booking_id=b_id,
                user=request.user,
                customer_name=data.get('customer_name', 'Walk-in Customer'),
                customer_phone=data.get('customer_phone', ''),
                vehicle_number=data.get('vehicle_number', ''),
                parking_lot=lot,
                slot=slot,
                vehicle_type=slot.vehicle_type,
                booking_start_datetime=start,
                booking_end_datetime=end,
                booking_duration_minutes=duration_minutes,
                date=start.date(),
                time_slot_id=f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}",
                price=price,
                status='confirmed',
                payment_status='paid',
                payment_method='manual_qr'
            )

            Transaction.objects.create(
                user=request.user,
                owner=lot.owner,
                booking=booking,
                amount=price,
                type='earning',
                status='completed',
                payment_method='cash',
                description=f"Manual booking for slot {slot.slot_number} at {lot.name}"
            )

            created_bookings.append(booking.booking_id)

        return JsonResponse({'message': 'Manual booking saved successfully', 'bookings': created_bookings}, status=201)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@login_required
def api_owner_bookings(request):
    owner = request.user
    lot_ids = ParkingLot.objects.filter(owner=owner).values_list('id', flat=True)
    query = Booking.objects.filter(parking_lot__in=lot_ids).select_related('parking_lot', 'slot', 'user')

    status = request.GET.get('status')
    if status and status != 'all':
        now = timezone.now()
        if status == 'active_now':
            query = query.filter(booking_start_datetime__lte=now, booking_end_datetime__gte=now, status__in=['active', 'attended', 'confirmed'])
        elif status == 'today':
            query = query.filter(date=now.date())
        else:
            query = query.filter(status=status)

    search = request.GET.get('search')
    if search:
        s = search.strip().upper()
        query = query.filter(
            Q(booking_id__icontains=s) |
            Q(vehicle_number__icontains=s) |
            Q(customer_name__icontains=s) |
            Q(customer_phone__icontains=s)
        )

    bookings_list = []
    for b in query.order_by('-created_at')[:50]:
        bookings_list.append({
            'id': b.id,
            'booking_id': b.booking_id,
            'customer_name': b.customer_name or (b.user.username if b.user else 'Guest'),
            'customer_phone': b.customer_phone or 'N/A',
            'vehicle_number': b.vehicle_number or 'N/A',
            'vehicle_type': b.vehicle_type,
            'slot_number': b.slot.slot_number,
            'lot_name': b.parking_lot.name,
            'date': b.date.strftime('%Y-%m-%d'),
            'time_slot': b.time_slot_id,
            'price': float(b.price),
            'status': b.status,
            'payment_status': b.payment_status,
        })

    return JsonResponse({'data': bookings_list})


@login_required
@require_POST
def api_verify_booking(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        booking_id = data.get('booking_id', '').strip().upper()

        booking = Booking.objects.filter(booking_id=booking_id).select_related('parking_lot', 'slot').first()
        if not booking:
            return JsonResponse({'success': False, 'message': 'Booking ID not found.'}, status=404)

        if booking.parking_lot.owner != request.user:
            return JsonResponse({'success': False, 'message': 'Unauthorized. Booking belongs to another facility.'}, status=403)

        if booking.status in ['completed', 'expired', 'cancelled']:
            return JsonResponse({'success': False, 'message': f'Invalid status. Booking is already {booking.status}.'}, status=422)

        if booking.status == 'attended':
            return JsonResponse({'success': False, 'message': 'Vehicle is already checked in (attended).'}, status=422)

        now = timezone.now()
        if now > booking.booking_end_datetime:
            return JsonResponse({'success': False, 'message': 'Booking time has expired.'}, status=422)

        # Allow 30 mins grace window before start
        if now < (booking.booking_start_datetime - timedelta(minutes=30)):
            return JsonResponse({'success': False, 'message': 'Too early for check-in. Verification opens 30 minutes before start time.'}, status=422)

        return JsonResponse({
            'success': True,
            'message': 'Valid Parking Ticket',
            'booking': {
                'id': booking.id,
                'booking_id': booking.booking_id,
                'customer_name': booking.customer_name or 'Guest',
                'customer_phone': booking.customer_phone or 'N/A',
                'vehicle_number': booking.vehicle_number or 'N/A',
                'vehicle_type': booking.vehicle_type,
                'slot_number': booking.slot.slot_number,
                'date': booking.date.strftime('%d %b %Y'),
                'time_slot': booking.time_slot_id,
                'status': booking.status,
                'price': float(booking.price),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def api_mark_attended(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        booking_id = data.get('booking_id')

        booking = Booking.objects.filter(Q(id=booking_id) | Q(booking_id=str(booking_id).upper())).first()
        if not booking:
            return JsonResponse({'success': False, 'message': 'Booking not found.'}, status=404)

        if booking.parking_lot.owner != request.user:
            return JsonResponse({'success': False, 'message': 'Unauthorized.'}, status=403)

        booking.status = 'attended'
        booking.attended_at = timezone.now()
        booking.verified_by = request.user
        booking.save()

        return JsonResponse({
            'success': True,
            'message': f'Check-in successful! Attendance marked for #{booking.booking_id}.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
