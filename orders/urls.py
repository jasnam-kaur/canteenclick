from django.urls import path
from . import views

urlpatterns = [
    path('add-to-cart/<int:variation_id>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('cart/', views.view_cart, name='view-cart'),
    path('place-order/', views.place_order, name='place-order'),
    path('order-complete/<uuid:order_id>/', views.order_complete, name='order-complete'),
    path('check-status/<int:order_id>/', views.check_order_status, name='check-order-status'),
    path('track-order/<int:order_id>/', views.live_track_order, name='live-track-order'),
    path('my-orders/', views.order_history, name='order-history'),
]