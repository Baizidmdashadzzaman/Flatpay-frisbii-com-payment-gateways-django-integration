def rent_bike(request):
    from django.contrib import messages
    from accounts.models import Customer, BikeBooking, BikeBookingAddon, Bike
    from django.contrib.auth.models import User
    from django.utils.crypto import get_random_string

    if request.method == 'POST':
        bike_id = request.POST.get('bike_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address', '')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        bike_quantity = request.POST.get('bike_quantity', 1)
        other_info = request.POST.get('other_info', '')

        bike = get_object_or_404(Bike, id=bike_id)
        
        customer = None
        user = request.user
        
        if not user.is_authenticated:
            if email:
                user_exists = User.objects.filter(email=email).exists()
                if user_exists:
                    user = User.objects.get(email=email)
                else:
                    password = get_random_string(length=10)
                    username = email
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=name or 'Guest'
                        )
                        # Optional: send email here
                    except Exception as e:
                        messages.error(request, f"Error creating account: {str(e)}")
                        user = None
        
        if user:
            try:
                customer, created = Customer.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': phone,
                    }
                )
                if not created and not customer.phone and phone:
                    customer.phone = phone
                if not customer.address and address:
                    customer.address = address
                customer.save()
            except Exception as e:
                messages.error(request, f"Error with customer profile: {str(e)}")

        try:
            booking = BikeBooking(
                customer=customer,  # can be none if user creation failed, though model allows null
                name=name,
                email=email,
                phone=phone,
                address=address,
                other_info=other_info,
                bike=bike,
                bike_quantity=int(bike_quantity) if bike_quantity else 1,
            )
            if start_date:
                booking.start_date = start_date
            if end_date:
                booking.end_date = end_date
            if start_time:
                booking.start_time = start_time
            if end_time:
                booking.end_time = end_time
                
            booking.save()
            booking.refresh_from_db()
            
            # Process Addons
            for ba in bike.bike_addons.all():
                quantity_str = request.POST.get(f'addon_quantity_{ba.id}', '0')
                try:
                    qty = int(quantity_str)
                    if qty > 0:
                        BikeBookingAddon.objects.create(
                            booking=booking,
                            addon=ba.addon,
                            price=ba.price,
                            quantity=qty
                        )
                except ValueError:
                    pass
            
            # Update the totals
            total_addons = sum(addon.total_price_with_days for addon in booking.booking_addons.all())
            booking.subtotal = booking.bike_total_price_with_days + total_addons
            booking.total = booking.subtotal
            booking.save()
            
            if getattr(settings, 'USE_PAYMENT_GATEWAY', False):
                import requests
                from django.urls import reverse
                
                api_key = getattr(settings, 'FLATPAY_KEY', '')
                url = 'https://checkout-api.frisbii.com/v1/session/charge'
                
                amount = int(float(booking.total) * 100)
                accept_url = request.build_absolute_uri(reverse('rent_bike_payment_accept', args=[booking.booking_number]))
                cancel_url = request.build_absolute_uri(reverse('rent_bike_payment_cancel', args=[booking.booking_number]))
                
                data = {
                    'order': {
                        'handle': booking.booking_number,
                        'amount': amount,
                        'currency': 'DKK',
                        'customer': {
                            'email': booking.email,
                            'first_name': booking.name.split()[0] if booking.name else 'Guest',
                            'last_name': ' '.join(booking.name.split()[1:]) if booking.name and len(booking.name.split()) > 1 else 'Guest',
                        }
                    },
                    'accept_url': accept_url,
                    'cancel_url': cancel_url
                }
                
                try:
                    response = requests.post(url, auth=(api_key, ''), json=data)
                    response_data = response.json()
                    if 'url' in response_data:
                        return redirect(response_data['url'])
                    else:
                        messages.error(request, f"Payment gateway error: {response_data.get('error', 'Unknown error')}")
                        return redirect('rent_bike_confirmation', booking_number=booking.booking_number)
                except Exception as e:
                    messages.error(request, f"Payment gateway error: {str(e)}")
                    return redirect('rent_bike_confirmation', booking_number=booking.booking_number)
            else:
                messages.success(request, f'Your bike booking has been submitted successfully! Booking Number: {booking.booking_number}')
                return redirect('rent_bike_confirmation', booking_number=booking.booking_number)
        except Exception as e:
            messages.error(request, f'An error occurred while booking: {str(e)}')

    bikes = Bike.objects.prefetch_related('bike_addons__addon').all().order_by('id')
    context = {
        'bikes': bikes,
    }
    return render(request, 'frontend/pages/rent-bike/rent_bike_list.html', context)
