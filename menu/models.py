from django.db import models
from django.contrib.auth.models import User

class Vendor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor', null=True, blank=True)
    def __str__(self):
        
        return self.name

class Counter(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, null=True)
    
    # === ADD THIS LINE ===
    image = models.ImageField(upload_to='counter_images/', blank=True, null=True) 

    def __str__(self):
        return self.name
    
class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    counter = models.ForeignKey(
        Counter, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name}"

class ItemVariation(models.Model):
    menu_item = models.ForeignKey(
        MenuItem, 
        on_delete=models.CASCADE, 
        related_name="variations" 
    )
    name = models.CharField(max_length=100) # e.g., "Cup", "Tub", "Small", "Large"
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        # --- THIS IS FIX #1 ---
        # I am checking if menu_item exists to be safe,
        # but the main fix is using 'menu_item.name'
        if self.menu_item:
            return f"{self.menu_item.name} ({self.name})"
        return f"Unnamed Variation ({self.name})"
    
    
class ReadyToEatItem(models.Model):
    item_variation = models.ForeignKey(ItemVariation, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.item_variation.menu_item.name} at {self.counter.name}"