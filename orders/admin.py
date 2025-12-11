from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem # Add Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item_variation', 'quantity', 'price_at_order'] # read-only in admin

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_price', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
    readonly_fields = ['user', 'total_price', 'order_id', 'created_at', 'updated_at', 'completed_at']


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)