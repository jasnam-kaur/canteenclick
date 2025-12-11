from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # This makes '/menu/' the main page for this app
    path('', views.menu_list, name='menu-list'),
    path('ready-to-eat/', views.ready_to_eat_list, name='ready-to-eat-list'),
    path('counter/<int:counter_id>/', views.counter_menu, name='counter_menu'),
    path('add-rte-to-cart/<int:rte_item_id>/', views.add_rte_to_cart, name='add-rte-to-cart'),
]