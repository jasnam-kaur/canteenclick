from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

# Import models from this app
from .models import Counter, MenuItem, ReadyToEatItem, ItemVariation

# Import models from the orders app
from orders.models import Cart, CartItem

def menu_list(request):
    # Get all counters from the database, ordered by their name
    counters = Counter.objects.order_by('name')
    
    context = {
        'counters': counters
    }
    return render(request, 'menu/menu_list.html', context)

def counter_menu(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)
    # Prefetch variations to avoid N+1 queries
    items = MenuItem.objects.filter(counter=counter).prefetch_related('variations')
    
    context = {
        'counter': counter,
        'items': items
    }
    return render(request, 'menu/counter_menu.html', context)

@login_required
def ready_to_eat_list(request):
    # 1. Start with items that are NOT sold (not in any order)
    filters = Q(claimed_by_order_item__isnull=True)

    if request.user.is_authenticated:
        # 2. Show items that are (Not in ANY cart) OR (In MY cart)
        filters &= (Q(cartitem__isnull=True) | Q(cartitem__cart__user=request.user))
    else:
        # Guest users see only items not in any cart
        filters &= Q(cartitem__isnull=True)

    rte_items = ReadyToEatItem.objects.filter(filters).select_related('item_variation__menu_item', 'counter')
    
    return render(request, 'menu/ready_to_eat.html', {'ready_to_eat_items': rte_items})

@login_required
# CHANGE 'rte_id' TO 'rte_item_id' HERE:
def add_rte_to_cart(request, rte_item_id):
    with transaction.atomic():
        try:
            # Use 'rte_item_id' inside the query too:
            rte_item = ReadyToEatItem.objects.select_for_update().get(
                id=rte_item_id,  # <--- Updated variable
                cartitem__isnull=True,
                claimed_by_order_item__isnull=True 
            )
        except ReadyToEatItem.DoesNotExist:
            messages.error(request, "Sorry, this item was just claimed by someone else!")
            return redirect('menu:ready-to-eat-list')

        cart, _ = Cart.objects.get_or_create(user=request.user)

        CartItem.objects.create(
            cart=cart,
            item_variation=rte_item.item_variation,
            quantity=1,
            claimed_rte_item=rte_item 
        )

        messages.success(request, "Item secured! It is now reserved in your cart.")
        return redirect('view-cart')