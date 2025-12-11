import uuid
from django.db import models
from django.contrib.auth.models import User
from menu.models import ItemVariation # We can import ItemVariation safely

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")

    item_variation = models.ForeignKey(ItemVariation, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    claimed_rte_item = models.OneToOneField(
        'menu.ReadyToEatItem', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cartitem'
    )

    def __str__(self):
        return f"{self.quantity} x {self.item_variation.menu_item.name} ({self.item_variation.name})"

    def get_total_price(self):
        return self.quantity * self.item_variation.price

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Ready for Pickup', 'Ready for Pickup'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    CANCELLED_BY_CHOICES = (
        ('vendor', 'Vendor'),
        ('user', 'User'),
    )
    cancellation_reason = models.CharField(max_length=255, blank=True, null=True)
    cancelled_by = models.CharField(max_length=10, choices=CANCELLED_BY_CHOICES, blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    is_ready_to_eat_purchase = models.BooleanField(default=False)
    
    # Razorpay Fields
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    order_id_razorpay = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    # QR Code Fields
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pickup_code = models.CharField(max_length=10, blank=True, null=True, unique=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username} - {self.status}"
    
    @property
    def time_taken_to_complete(self):
        if self.completed_at and self.created_at:
            time_diff = self.completed_at - self.created_at
            return time_diff.total_seconds()
        return None

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_variation = models.ForeignKey(ItemVariation, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=6, decimal_places=2)
    
    claimed_rte_item = models.OneToOneField(
        'menu.ReadyToEatItem', # Correct string reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claimed_by_order_item'
    )