import random
import qrcode
from io import BytesIO
import base64

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

from menu.models import ItemVariation
from .models import Cart, CartItem, Order, OrderItem

@login_required
def add_to_cart(request, variation_id):
    try:
        # Get the specific item variation the user wants to add
        item_variation = ItemVariation.objects.get(id=variation_id)
    except ItemVariation.DoesNotExist:
        messages.error(request, "That item does not exist.")
        return redirect('core:home')
    
    # Get the logged-in user's cart
    user_cart, created = Cart.objects.get_or_create(user=request.user)    
    
    # Check if this item is already in the cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=user_cart,
        item_variation=item_variation
    )
    
    # If it's not a new item (created=False), just increase the quantity
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Added another {item_variation.menu_item.name} ({item_variation.name}) to your cart.")
    else:
        messages.success(request, f"Added {item_variation.menu_item.name} ({item_variation.name}) to your cart.")
    
    # Redirect back to the menu they were on
    counter_id = item_variation.menu_item.counter.id
    return redirect('menu:counter_menu', counter_id=counter_id)


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('item_variation__menu_item').all()
    
    total_price = 0
    for item in cart_items:
        total_price += item.get_total_price()
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'orders/cart.html', context)


@login_required
def remove_from_cart(request, cart_item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
        item_name = cart_item.item_variation.menu_item.name
        cart_item.delete()
        messages.success(request, f"Removed {item_name} from your cart.")
    except Exception as e:
        messages.error(request, f"Error removing item: {e}")

    return redirect('view-cart')


@login_required
@transaction.atomic
def place_order(request):
    """
    Standard 'Cash on Pickup' flow.
    1. Creates Order.
    2. Moves items from Cart -> Order.
    3. Transfers RTE locks.
    4. Clears Cart.
    5. Redirects to Success Page.
    """
    if request.method == 'POST':
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('view-cart')

        # 1. Calculate Total
        total_price = 0
        for item in cart_items:
            total_price += item.get_total_price()

        # 2. Create Order
        order = Order(
            user=request.user,
            total_price=total_price,
            status='Pending',
            is_paid=False # Cash on Pickup
        )

        # Generate unique pickup code
        while True:
            code = str(random.randint(10000, 99999))
            if not Order.objects.filter(pickup_code=code).exists():
                order.pickup_code = code
                break 
        order.save() 

        # 3. Create OrderItems (Transfer RTE lock here)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                item_variation=item.item_variation,
                quantity=item.quantity,
                price_at_order=item.item_variation.price,
                # CRITICAL: Transfer the lock so the item disappears from the RTE menu
                claimed_rte_item=item.claimed_rte_item 
            )
        
        # 4. Clear the cart
        # Since we moved the 'claimed_rte_item' reference to OrderItem above,
        # deleting the CartItem is now safe.
        cart.items.all().delete()
        
        messages.success(request, "Order placed successfully! Pay at the counter.")
        return redirect('order-complete', order_id=order.order_id)

    else:
        messages.error(request, "Invalid request.")
        return redirect('view-cart')


@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Generate QR Code
    qr_img = qrcode.make(str(order.pickup_code))
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'order': order,
        'qr_base64': qr_base64
    }
    return render(request, 'orders/order_complete.html', context)


@login_required
def check_order_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        if order.status == 'Completed':
            return JsonResponse({
                'status': 'Completed',
                'total_price': order.total_price,
                'completed_at': order.completed_at.strftime('%d %b %Y, %H:%M') 
            })
        else:
            return JsonResponse({'status': order.get_status_display()})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'Not Found'}, status=404)


@login_required
def live_track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/live_tracking.html', {'order': order})


@login_required
def order_history(request):
    my_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': my_orders})