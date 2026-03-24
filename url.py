path('rent-bike/', views.rent_bike, name='rent_bike'),
path('rent-bike/confirmation/<str:booking_number>/', views.rent_bike_confirmation, name='rent_bike_confirmation'),
path('rent-bike/payment/accept/<str:booking_number>/', views.rent_bike_payment_accept, name='rent_bike_payment_accept'),
path('rent-bike/payment/cancel/<str:booking_number>/', views.rent_bike_payment_cancel, name='rent_bike_payment_cancel'),
    
