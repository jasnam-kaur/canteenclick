from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('order-history/', views.order_history, name='order-history'),
    path('order/cancel/<int:order_id>/', views.cancel_order_user, name='user-cancel-order'),

    
    path('password-reset/find-user/', 
         views.reset_password_find_user, 
         name='reset_password_find_user'),

    path('password-reset/set-new/', 
         views.set_new_password, 
         name='set_new_password'),
]