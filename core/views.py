from django.shortcuts import render
from menu.models import Counter  # Import your Counter model from the 'menu' app

def home(request):
    """
    This view fetches all active counters to display them
    on the homepage as cards.
    """
    # Get all Counter objects from the database
    all_counters = Counter.objects.all()
    
    # Create a 'context' dictionary to pass this data to the template
    context = {
        'counters': all_counters
    }
    
    # Render the 'home.html' template with the context data
    return render(request, 'home.html', context)