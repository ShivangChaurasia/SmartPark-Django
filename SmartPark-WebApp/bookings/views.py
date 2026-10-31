import json
import random
import string
import hmac
import hashlib
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Sum, F
from django.conf import settings
from django.contrib import messages
import razorpay

from parking.models import ParkingLot, Slot
from .models import Booking, Transaction
from .ticket_generator import generate_ticket_pdf


@login_required
def checkout_page(request):
    lot_id = request.GET.get('lot_id')
    lot = get_object_or_404(ParkingLot, pk=lot_id) if lot_id else None
    if not lot:
        return redirect('search')

    is_host = getattr(request.user, 'role', '') == 'host'
    is_owner = (lot.owner_id == request.user.id)

    # Restriction: Hosts can only reserve slots at their own facility for walk-in customers
    if is_host and not is_owner:
        messages.warning(
            request,
            "Host Mode Active: You cannot reserve spots at other facilities. Switch to Driver Mode to book as a customer."
        )
        return redirect('parking_detail', pk=lot.id)

    slot_ids = request.GET.get('slot_ids', '')
    start_str = request.GET.get('start_datetime', '')
    end_str = request.GET.get('end_datetime', '')

    selected_slots = []
    if slot_ids:
        s_list = [s.strip() for s in slot_ids.split(',') if s.strip()]
        selected_slots = Slot.objects.filter(id__in=s_list, parking_lot=lot)

    # Compute outstanding no-show penalty for this user (manual_qr no-shows not yet collected)
    now_co = timezone.now()
    # First auto-expire any bookings whose window has passed
    Booking.objects.filter(
        user=request.user,
        payment_method='manual_qr',
        status__in=['upcoming', 'active'],
        booking_end_datetime__lt=now_co,
        penalty_applied=False,
    ).update(status='cancelled', no_show_penalty=F('price'), cancelled_at=now_co)

    outstanding_penalty = float(
        Booking.objects.filter(
            user=request.user,
            payment_method='manual_qr',
            status='cancelled',
            no_show_penalty__gt=0,
            penalty_applied=False,
        ).aggregate(total=Sum('no_show_penalty'))['total'] or 0
    )

    context = {
        'lot': lot,
        'selected_slots': selected_slots,
        'slot_ids': slot_ids,
        'start_datetime': start_str,
        'end_datetime': end_str,
        'razorpay_key': getattr(settings, 'RAZORPAY_KEY', ''),
        'is_host_booking': is_host and is_owner,
        'outstanding_penalty': outstanding_penalty,
    }
    return render(request, 'bookings/checkout.html', context)


@login_required
@require_POST
def api_create_order(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        lot_id = data.get('parking_lot_id')
        slot_ids = data.get('slot_ids', [])
        if isinstance(slot_ids, str):
            slot_ids = [slot_ids]

        start_str = data.get('start_datetime')
        end_str = data.get('end_datetime')
        amount = float(data.get('amount', 0))

        start = timezone.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end = timezone.datetime.fromisoformat(end_str.replace('Z', '+00:00'))

        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())

        lot = get_object_or_404(ParkingLot, pk=lot_id)

        # Host booking rule validation: Host can only book at their own facility
        is_host = getattr(request.user, 'role', '') == 'host'
        if is_host and lot.owner_id != request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'Host Mode Active: You can only book slots at your own facility for walk-in customers. Switch to Driver Mode to book at other facilities.'
            }, status=403)

        # Double check collision
        for sid in slot_ids:
            slot = get_object_or_404(Slot, pk=sid, parking_lot=lot)
            if Booking.objects.filter(
                parking_lot=lot,
                slot=slot,
                status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
                booking_start_datetime__lt=end,
                booking_end_datetime__gt=start
            ).exists():
                return JsonResponse({
                    'success': False,
                    'message': f"Slot {slot.slot_number} has just been reserved by someone else. Please choose another."
                }, status=409)

        # Razorpay integration
        razorpay_key = getattr(settings, 'RAZORPAY_KEY', '')
        razorpay_secret = getattr(settings, 'RAZORPAY_SECRET', '')

        if razorpay_key and razorpay_secret:
            client = razorpay.Client(auth=(razorpay_key, razorpay_secret))
            order_data = {
                'amount': int(round(amount * 100)),  # in paise
                'currency': 'INR',
                'receipt': f"rcpt_{int(timezone.now().timestamp())}",
                'payment_capture': 1
            }
            order = client.order.create(data=order_data)
            return JsonResponse({
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'key': razorpay_key
            })
        elif razorpay_key:
            # Client-side checkout using Razorpay Test Key ID
            return JsonResponse({
                'success': True,
                'order_id': None,
                'amount': int(round(amount * 100)),
                'currency': 'INR',
                'key': razorpay_key
            })
        else:
            # Fallback mock order for instant local testing without live API keys
            mock_order_id = f"order_mock_{int(timezone.now().timestamp())}"
            return JsonResponse({
                'success': True,
                'order_id': mock_order_id,
                'amount': int(round(amount * 100)),
                'currency': 'INR',
                'key': 'rzp_test_mock'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def api_create_booking(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        lot_id = data.get('parking_lot_id')
        slot_ids = data.get('slot_ids', [])
        if isinstance(slot_ids, str):
            slot_ids = [slot_ids]

        start_str = data.get('start_datetime')
        end_str = data.get('end_datetime')
        payment_method = data.get('payment_method', 'razorpay')

        start = timezone.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end = timezone.datetime.fromisoformat(end_str.replace('Z', '+00:00'))

        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())

        lot = get_object_or_404(ParkingLot, pk=lot_id)

        # Host booking rule validation: Host can only book at their own facility
        is_host = getattr(request.user, 'role', '') == 'host'
        if is_host and lot.owner_id != request.user.id:
            return JsonResponse({
                'message': 'Host Mode Active: You can only book slots at your own facility for walk-in customers. Switch to Driver Mode to book at other facilities.'
            }, status=403)

        is_host_booking = bool(is_host and lot.owner_id == request.user.id)
        duration_minutes = int((end - start).total_seconds() // 60)

        # --- No-show penalty detection (manual_qr bookings only) ---
        # Scan the user's past manual_qr bookings whose window has already ended but were
        # never cancelled and never attended (no-show). Mark them and collect 100% penalty
        # on the current booking total if payment_method is manual_qr.
        now_check = timezone.now()
        no_show_bookings = Booking.objects.filter(
            user=request.user,
            payment_method='manual_qr',
            status__in=['upcoming', 'active'],
            booking_end_datetime__lt=now_check,
            penalty_applied=False,
        )
        outstanding_penalty = 0.0
        for ns in no_show_bookings:
            ns.status = 'cancelled'
            ns.no_show_penalty = ns.price
            ns.refund_amount = 0.0
            ns.refund_status = 'none'
            ns.cancelled_at = now_check
            ns.penalty_applied = False  # Will be marked True when penalty is collected below
            ns.save()
            outstanding_penalty += float(ns.price)

        # Razorpay signature verification if live keys and razorpay method used
        if payment_method == 'razorpay':
            order_id = data.get('razorpay_order_id', '')
            payment_id = data.get('razorpay_payment_id', '')
            signature = data.get('razorpay_signature', '')
            secret = getattr(settings, 'RAZORPAY_SECRET', '')

            if secret and not order_id.startswith('order_mock_'):
                # Verify HMAC SHA256 signature
                msg = f"{order_id}|{payment_id}".encode()
                generated_signature = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
                if generated_signature != signature:
                    return JsonResponse({'message': 'Invalid payment signature. Verification failed.'}, status=400)

        bookings_created = []
        for sid in slot_ids:
            slot = get_object_or_404(Slot, pk=sid, parking_lot=lot)

            # Prevent double booking collision
            if Booking.objects.filter(
                parking_lot=lot,
                slot=slot,
                status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
                booking_start_datetime__lt=end,
                booking_end_datetime__gt=start
            ).exists():
                return JsonResponse({'message': f"Slot {slot.slot_number} is already booked."}, status=409)

            hourly = lot.car_price if slot.vehicle_type == 'car' else (lot.bike_price if slot.vehicle_type == 'bike' else lot.bus_price)
            price = (duration_minutes / 60) * float(hourly)

            b_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

            now = timezone.now()
            status = 'upcoming'
            if now >= start and now <= end:
                status = 'active'

            # Determine payment & transaction status
            if is_host_booking:
                # Host/Owner booking directly for walk-in customer at the gate desk
                payment_status = 'paid'
                txn_status = 'completed'
                cust_name = data.get('customer_name') or 'Walk-In Customer'
                cust_phone = data.get('customer_phone') or ''
                cust_email = data.get('email') or request.user.email
            else:
                payment_status = 'paid' if payment_method == 'razorpay' else 'pending_verification'
                txn_status = 'completed' if payment_method == 'razorpay' else 'pending'
                cust_name = data.get('customer_name') or request.user.get_full_name() or request.user.username
                cust_phone = data.get('customer_phone') or getattr(request.user, 'phone', '') or ''
                cust_email = data.get('email') or request.user.email

            booking = Booking.objects.create(
                booking_id=b_id,
                user=request.user,
                booking_email=cust_email,
                customer_name=cust_name,
                customer_phone=cust_phone,
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
                status=status,
                payment_status=payment_status,
                payment_method=payment_method,
                razorpay_order_id=data.get('razorpay_order_id'),
                razorpay_payment_id=data.get('razorpay_payment_id'),
                invoice_number=f"INV-{b_id}"
            )

            # Record financial transaction for this booking
            Transaction.objects.create(
                user=request.user,
                owner=lot.owner,
                booking=booking,
                amount=price,
                type='payment',
                status=txn_status,
                payment_method=payment_method,
                description=f"{'Walk-in customer' if is_host_booking else 'Driver'} reservation for slot {slot.slot_number} at {lot.name}"
            )

            # Collect outstanding no-show penalties on first manual_qr booking slot
            if outstanding_penalty > 0 and payment_method == 'manual_qr' and not is_host_booking:
                Transaction.objects.create(
                    user=request.user,
                    owner=lot.owner,
                    booking=booking,
                    amount=outstanding_penalty,
                    type='payment',
                    status='pending',
                    payment_method='manual_qr',
                    description=f"No-show penalty carried forward from previous bookings: ₹{outstanding_penalty:.2f}"
                )
                # Mark all pending no-show source bookings as penalty collected
                Booking.objects.filter(
                    user=request.user,
                    payment_method='manual_qr',
                    status='cancelled',
                    penalty_applied=False,
                    no_show_penalty__gt=0,
                ).update(penalty_applied=True)
                outstanding_penalty = 0.0  # Only charge once (on first slot in this booking batch)

            # Also create corresponding earning transaction for the host
            Transaction.objects.create(
                user=request.user,
                owner=lot.owner,
                booking=booking,
                amount=price,
                type='earning',
                status=txn_status,
                payment_method=payment_method,
                description=f"Host earning for slot {slot.slot_number} at {lot.name}"
            )

            bookings_created.append({
                'id': booking.id,
                'booking_id': booking.booking_id,
                'slot_number': slot.slot_number,
                'price': float(booking.price),
            })

        return JsonResponse({
            'message': 'Bookings confirmed successfully',
            'bookings': bookings_created
        }, status=201)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@login_required
def user_dashboard(request):
    user = request.user
    bookings = Booking.objects.filter(
        Q(user=user) | Q(booking_email=user.email)
    ).select_related('parking_lot', 'slot').order_by('-booking_start_datetime')

    now = timezone.now()
    categorized = {
        'active': [],
        'upcoming': [],
        'completed': [],
        'cancelled': []
    }

    for b in bookings:
        if b.status == 'cancelled':
            categorized['cancelled'].append(b)
        elif b.status == 'attended' or (now >= b.booking_start_datetime and now <= b.booking_end_datetime):
            categorized['active'].append(b)
        elif now < b.booking_start_datetime:
            categorized['upcoming'].append(b)
        else:
            categorized['completed'].append(b)

    transactions = Transaction.objects.filter(user=user, type__in=['payment', 'refund'])

    total_spent = transactions.filter(type='payment', status='completed').aggregate(t=Sum('amount'))['t'] or 0
    total_refunds = transactions.filter(type='refund', status='completed').aggregate(t=Sum('amount'))['t'] or 0

    # Calculate outstanding no-show penalty (unpaid, not yet collected)
    outstanding_penalty = Booking.objects.filter(
        user=user,
        payment_method='manual_qr',
        status='cancelled',
        no_show_penalty__gt=0,
        penalty_applied=False,
    ).aggregate(total=Sum('no_show_penalty'))['total'] or 0

    stats = {
        'total_bookings': bookings.count(),
        'active_sessions': len(categorized['active']),
        'total_spent': total_spent,
        'total_refunds': total_refunds,
        'outstanding_penalty': float(outstanding_penalty),
    }

    context = {
        'categorized': categorized,
        'transactions': transactions[:10],
        'stats': stats,
        'outstanding_penalty': float(outstanding_penalty),
    }
    return render(request, 'bookings/dashboard.html', context)


@login_required
@require_POST
def api_cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.user != request.user and booking.booking_email != request.user.email:
        return JsonResponse({'message': 'Unauthorized action.'}, status=403)

    if booking.status == 'cancelled':
        return JsonResponse({'message': 'Booking is already cancelled.'}, status=400)

    now = timezone.now()
    diff_minutes = (booking.booking_start_datetime - now).total_seconds() / 60.0

    # --- Pay-at-Site (manual_qr) Hard Lock: Cannot cancel within 60 minutes of start ---
    # If the booking window starts in < 60 minutes (or has already started), cancellation
    # is locked. The slot is held; if the customer is a no-show, 100% penalty is carried
    # forward to their next booking.
    if booking.payment_method == 'manual_qr' and diff_minutes < 60:
        return JsonResponse({
            'message': (
                'Cancellation is locked for Pay-at-Site reservations within 1 hour of start time. '
                'If you do not arrive, the full booking charge (₹{:.2f}) will be added as a penalty '
                'to your next booking.'.format(float(booking.price))
            ),
            'locked': True,
            'penalty_amount': float(booking.price),
        }, status=400)

    # Tiered refund algorithm for online-paid (razorpay) bookings:
    # >= 120 mins -> 100%
    # >= 30 mins  -> 50%
    # < 30 mins   -> 0%
    # For manual_qr (when cancellation IS allowed, i.e. > 60 mins before): full cancellation, no charge.
    if booking.payment_method == 'manual_qr':
        # No money was paid yet; simply release the slot.
        refund_pct = 0
        refund_amount = 0.0
        refund_status = 'none'
    else:
        if diff_minutes >= 120:
            refund_pct = 100
        elif diff_minutes >= 30:
            refund_pct = 50
        else:
            refund_pct = 0
        refund_amount = (float(booking.price) * refund_pct) / 100.0
        refund_status = 'completed' if refund_amount > 0 else 'none'

    booking.status = 'cancelled'
    booking.refund_amount = refund_amount
    booking.refund_status = refund_status
    booking.cancelled_at = now
    booking.save()

    if refund_amount > 0:
        Transaction.objects.create(
            user=request.user,
            owner=booking.parking_lot.owner,
            booking=booking,
            amount=refund_amount,
            type='refund',
            status='completed',
            payment_method=booking.payment_method,
            description=f"Refund ({refund_pct}%) for cancelled booking #{booking.booking_id}"
        )

    return JsonResponse({
        'message': 'Booking cancelled successfully',
        'refund_amount': refund_amount,
        'refund_percentage': refund_pct,
        'payment_method': booking.payment_method,
    })


@login_required
@require_POST
def api_extend_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.user != request.user and booking.booking_email != request.user.email:
        return JsonResponse({'message': 'Unauthorized action.'}, status=403)

    if booking.status not in ['confirmed', 'active', 'attended']:
        return JsonResponse({'message': 'Only active bookings can be extended.'}, status=400)

    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        additional_minutes = int(data.get('additional_duration_minutes', 30))
    except (ValueError, TypeError):
        return JsonResponse({'message': 'Invalid duration.'}, status=400)

    new_end = booking.booking_end_datetime + timedelta(minutes=additional_minutes)

    # Collision check for the extension period
    collision = Booking.objects.filter(
        parking_lot=booking.parking_lot,
        slot=booking.slot,
        status__in=['confirmed', 'pending', 'active', 'upcoming', 'attended'],
        booking_start_datetime__lt=new_end,
        booking_end_datetime__gt=booking.booking_end_datetime
    ).exclude(id=booking.id).exists()

    if collision:
        return JsonResponse({'message': 'Slot is reserved by another user during the requested extension.'}, status=409)

    hourly = booking.parking_lot.car_price if booking.vehicle_type == 'car' else (
        booking.parking_lot.bike_price if booking.vehicle_type == 'bike' else booking.parking_lot.bus_price
    )
    extra_cost = (additional_minutes / 60) * float(hourly)

    booking.booking_end_datetime = new_end
    booking.booking_duration_minutes += additional_minutes
    booking.time_slot_id = f"{booking.booking_start_datetime.strftime('%H:%M')}-{new_end.strftime('%H:%M')}"
    booking.price = float(booking.price) + extra_cost
    booking.save()

    Transaction.objects.create(
        user=request.user,
        owner=booking.parking_lot.owner,
        booking=booking,
        amount=extra_cost,
        type='payment',
        status='completed',
        payment_method=booking.payment_method,
        description=f"Extension of {additional_minutes} mins for booking #{booking.booking_id}"
    )

    return JsonResponse({
        'message': 'Session extended successfully',
        'new_end_time': new_end.strftime('%I:%M %p'),
        'cost': extra_cost
    })


@login_required
def download_ticket(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.user != booking.user and request.user != booking.parking_lot.owner and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)

    pdf_bytes = generate_ticket_pdf(booking)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="SmartPark_Ticket_{booking.booking_id}.pdf"'
    return response


@login_required
def view_ticket(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.user != booking.user and request.user != booking.parking_lot.owner and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)

    pdf_bytes = generate_ticket_pdf(booking)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="SmartPark_Ticket_{booking.booking_id}.pdf"'
    return response
