from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from orders.models import Order
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST) 

        if form.is_valid(): 
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
        else:
            context = {'form': form}
            return render(request, 'users/signup.html', context)

    else:
        form = UserCreationForm() 
        context = {'form': form}
        return render(request, 'users/signup.html', context)
    

def login_view(request):
    if request.method == 'POST':
        # This is the logic for *submitting* the form
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"You are now logged in as {user.username}.")
                return redirect('core:home') # Redirect to homepage
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
            
    else:
        # This is the logic for *showing* the page (the GET request)
        form = AuthenticationForm()
    
    # --- THIS IS THE FIX ---
    # This line is now UN-INDENTED.
    # It will run for GET requests AND for invalid POST requests.
    return render(request, 'users/login.html', {'form': form})

@login_required
def order_history(request):
    # Get ALL orders for this user
    all_orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at') # Show newest first

    context = {
        'orders': all_orders
    }
    return render(request, 'users/order_history.html', context)

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('core:home')

def reset_password_find_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            # Check if the user exists
            user = User.objects.get(username=username)
            
            # If they exist, save their ID in the session and send them to the next step
            request.session['user_to_reset'] = user.id
            return redirect('set_new_password')
        
        except User.DoesNotExist:
            # If user not found, show an error
            messages.error(request, "User not found. Please check the username.")
    
    return render(request, 'users/reset_password_find_user.html')

def set_new_password(request):
    # Check if we know which user to reset (from the previous step)
    user_id = request.session.get('user_to_reset')
    
    if not user_id:
        # If not, send them back to step 1
        messages.error(request, "No user specified. Please find your user first.")
        return redirect('reset_password_find_user')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "An error occurred. Please try again.")
        return redirect('reset_password_find_user')

    if request.method == 'POST':
        # Use Django's built-in "Set Password" form for security
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save() # This saves the new password
            
            # Clear the session key
            del request.session['user_to_reset']
            
            messages.success(request, "Password reset successful! You can now log in.")
            return redirect('login')
        else:
            # If passwords don't match, the form will show the error
            pass
    else:
        # Show a blank "Set Password" form
        form = SetPasswordForm(user)

    context = {'form': form}
    return render(request, 'users/set_new_password.html', context)

@login_required
def cancel_order_user(request, order_id):
    # 1. Get the order, making sure it belongs to this user
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 2. CRITICAL: Security Check
    #    Only allow cancellation if the order is still "Pending"
    if order.status != 'Pending':
        messages.error(request, "This order is already being prepared and can no longer be cancelled.")
        return redirect('order-history')

    # 3. Handle the form submission
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Changed my mind') # Get reason from dropdown

        # 4. Update the order with all the new info
        order.status = 'Cancelled'
        order.cancellation_reason = reason
        order.cancelled_by = 'user' # Set who cancelled
        order.cancelled_at = timezone.now()
        order.save()

        messages.success(request, f"Order #{order.id} has been successfully cancelled.")
        return redirect('order-history')

    # 5. If it's a GET request, just show the confirmation page
    context = {
        'order': order
    }
    return render(request, 'users/cancel_order_confirm.html', context)