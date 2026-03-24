def rent_bike_payment_accept(request, booking_number):
    from accounts.models import BikeBooking
    from django.contrib import messages
    import requests
    
    booking = get_object_or_404(BikeBooking, booking_number=booking_number)
    
    if getattr(settings, 'USE_PAYMENT_GATEWAY', False):
        api_key = getattr(settings, 'FLATPAY_KEY', '')
        url = f"https://api.frisbii.com/v1/charge/{booking_number}"
        try:
            response = requests.get(url, auth=(api_key, ''), headers={'Accept': 'application/json'})
            data = response.json()
            if response.status_code == 200 and data.get('state') not in ['authorized', 'settled']:
                messages.error(request, "Payment was not authorized.")
                return redirect('rent_bike')
        except Exception as e:
            pass
            
    if booking.status != 'confirmed':
        booking.status = 'confirmed'
        booking.save()
        
    messages.success(request, f'Payment successful! Your bike booking confirmed. Booking Number: {booking.booking_number}')
    return redirect('rent_bike_confirmation', booking_number=booking.booking_number)
