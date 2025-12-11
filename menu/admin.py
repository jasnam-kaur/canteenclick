from django.contrib import admin
from .models import Vendor, Counter, MenuItem, ItemVariation, ReadyToEatItem

# This "inline" class lets us add Variations directly on the MenuItem page
class ItemVariationInline(admin.TabularInline):
    model = ItemVariation
    extra = 1 # Shows one extra blank "Variation" slot by default

class MenuItemAdmin(admin.ModelAdmin):
    # This tells the MenuItem admin page to include the ItemVariationInline
    inlines = [ItemVariationInline]

# Register your models
admin.site.register(Vendor)
admin.site.register(Counter)
admin.site.register(MenuItem, MenuItemAdmin) # We use the custom admin class here
admin.site.register(ReadyToEatItem)