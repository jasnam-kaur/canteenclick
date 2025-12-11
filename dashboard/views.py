from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from orders.models import Order
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from menu.models import ReadyToEatItem
from django.db import transaction

from django.utils import timezone # Make sure this is imported at the top

@login_required
def dashboard_home(request):
    if not request.user.is_staff:
        return redirect('home')
    
    vendor = request.user.vendor
    today = timezone.now().date()

    # Get a base query
    base_query = Order.objects.filter(
        items__item_variation__menu_item__counter__vendor=vendor  # <-- FIX 1
    ).distinct()

    # 1. Get ACTIVE orders
    active_orders = base_query.filter(
        status__in=['Pending', 'Preparing', 'Ready for Pickup']
    ).order_by('created_at')

    # 2. Get COMPLETED orders from TODAY
    completed_orders_today = base_query.filter(
        status='Completed',
        completed_at__date=today 
    ).order_by('-completed_at')
    
    # 3. Get CANCELLED orders from TODAY
    cancelled_orders_today = base_query.filter(
        status='Cancelled',
        updated_at__date=today 
    ).order_by('-updated_at')

    # Get the counts
    completed_count = completed_orders_today.count()
    cancelled_count = cancelled_orders_today.count()

    context = {
        'vendor_name': vendor.name,
        'active_orders': active_orders,
        'completed_orders_today': completed_orders_today,
        'completed_count': completed_count,
        'cancelled_orders_today': cancelled_orders_today,
        'cancelled_count': cancelled_count
    }
    return render(request, 'dashboard/home.html', context)

@login_required
def order_details(request, order_id):
    if not request.user.is_staff:
        return redirect('home')

    # We build a queryset first, filtering by ID and vendor
    queryset = Order.objects.filter(
        id=order_id,
        items__item_variation__menu_item__counter__vendor=request.user.vendor  # <-- FIX 2
    ).distinct()

    # Then we pass the unique queryset to get_object_or_404
    order = get_object_or_404(queryset)

    # This part handles the form submission
    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
            order.status = new_status

            # --- NEW: SAVE TIMESTAMPS ---
            if new_status == 'Preparing':
                order.preparing_at = timezone.now()
            elif new_status == 'Ready for Pickup':
                order.ready_at = timezone.now()
            # --- END NEW ---

            order.save()

            if new_status == 'Completed':
                for item in order.items.all():
                    if item.claimed_rte_item:
                        item.claimed_rte_item.delete()

            messages.success(request, f"Order #{order.id} status updated to {new_status}.")
            return redirect('dashboard-home')

    # This part handles the page load (GET request)
    order_items = order.items.all()
    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, 'dashboard/order_detail.html', context)

@login_required
def verify_pickup(request):
    if not request.user.is_staff:
        return redirect('home')
    
    context = {} # A context to pass to the template

    # This part handles the form submission
    if request.method == 'POST':
        code_from_form = request.POST.get('order_id')
        
        if not code_from_form:
            messages.error(request, "Please enter a Pickup Code.")
            
        else:
            try:
                # Find the active order by its pickup_code
                order = Order.objects.get(
                    pickup_code=code_from_form,
                    status__in=['Pending', 'Preparing', 'Ready for Pickup']
                )

                # Check if this order belongs to this vendor
                if not order.items.filter(item_variation__menu_item__counter__vendor=request.user.vendor).exists(): # <-- FIX 3
                    messages.error(request, "Order not found or does not belong to you.")
                
                else:
                    # SUCCESS: Mark as completed
                    order.status = 'Completed'
                    order.completed_at = timezone.now() # Set the completion time
                    order.save()
                    
                    messages.success(request, f"Order #{order.id} ({order.pickup_code}) verified and marked as 'Completed'!")
                    return redirect('dashboard-home')

            except Order.DoesNotExist:
                messages.error(request, "Invalid Pickup Code. No active order found.")
    
    return render(request, 'dashboard/verify_pickup.html', context)

@login_required
def cancel_order(request, order_id):
    if not request.user.is_staff:
        return redirect('core:home')
        
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'Cancelled by Vendor')
        
        # DEBUG PRINT: Check what the status actually is
        print(f"DEBUG: Cancelling Order #{order.id}. Current Status: '{order.status}'")

        # Check strictly for the statuses that imply food is cooked
        if order.status in ['Preparing', 'Ready for Pickup']:
            print("DEBUG: Status matches! Moving items to Ready-to-Eat...")
            
            for order_item in order.items.all():
                # Only proceed if this wasn't already a leftover claim
                if not order_item.claimed_rte_item:
                    
                    # Create 1 RTE entry for every quantity count
                    # e.g., 2 Burgers = 2 Separate RTE entries
                    for i in range(order_item.quantity):
                        try:
                            ReadyToEatItem.objects.create(
                                item_variation=order_item.item_variation,
                                counter=order_item.item_variation.menu_item.counter,
                                quantity=1  # <--- CRITICAL FIX: Database requires this field
                            )
                            print(f"DEBUG: Created RTE item for {order_item.item_variation.name}")
                        except Exception as e:
                            print(f"DEBUG: Error creating RTE item: {e}")
        else:
            print(f"DEBUG: Status '{order.status}' did not trigger RTE move.")
        
        order.status = 'Cancelled'
        order.cancellation_reason = reason
        order.cancelled_by = 'Vendor'
        order.save()
        
        messages.success(request, f"Order #{order.id} cancelled.")
        
    return redirect('dashboard-home')