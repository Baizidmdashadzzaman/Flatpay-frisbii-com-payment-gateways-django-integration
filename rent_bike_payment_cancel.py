def rent_bike_payment_cancel(request, booking_number):
    from accounts.models import BikeBooking
    from django.contrib import messages
    
    booking = get_object_or_404(BikeBooking, booking_number=booking_number)
    if booking.status != 'confirmed':
        booking.status = 'cancelled'
        booking.save()
        
    messages.warning(request, "Payment was cancelled.")
    return redirect('rent_bike')
