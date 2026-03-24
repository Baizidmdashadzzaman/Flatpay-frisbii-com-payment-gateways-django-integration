def rent_bike_confirmation(request, booking_number):
    from accounts.models import BikeBooking
    booking = get_object_or_404(BikeBooking.objects.prefetch_related('booking_addons__addon'), booking_number=booking_number)
    context = {
        'booking': booking,
    }
    return render(request, 'frontend/pages/rent-bike/confirmation.html', context)
