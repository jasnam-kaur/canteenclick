from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard-home'),
    path('order/<int:order_id>/', views.order_details, name='order-details'),
    path('verify/', views.verify_pickup, name='verify-pickup'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel-order'),
]