# Update the profile view in accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from events.models import Event, EventStatus
from tickets.models import Order, Ticket
from .forms import CustomUserCreationForm


def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
    }
    
    # For CUSTOMER users, show event statistics
    if user.role == 'CUSTOMER':
        events = Event.objects.filter(owner=user)
        context.update({
            'total_events': events.count(),
            'pending_events': events.filter(status=EventStatus.PENDING).count(),
            'approved_events': events.filter(status=EventStatus.APPROVED).count(),
            'rejected_events': events.filter(status=EventStatus.REJECTED).count(),
            'upcoming_events': events.filter(
                status=EventStatus.APPROVED,
                date_time__gte=timezone.now()
            ).order_by('date_time')[:5],
            'total_tickets_sold': Ticket.objects.filter(
                event__owner=user,
                order__status='COMPLETED'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'total_revenue': Ticket.objects.filter(
                event__owner=user,
                order__status='COMPLETED'
            ).aggregate(
                total=Sum('quantity') * Sum('unit_price')
            )['total'] or 0,
        })
    
    # For all users, show purchase statistics
    orders = Order.objects.filter(user=user)
    context.update({
        'total_orders': orders.count(),
        'completed_orders': orders.filter(status='COMPLETED').count(),
        'total_spent': orders.filter(status='COMPLETED').aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'upcoming_tickets': Ticket.objects.filter(
            order__user=user,
            order__status='COMPLETED',
            event__date_time__gte=timezone.now()
        ).select_related('event').order_by('event__date_time')[:5],
    })
    
    return render(request, 'accounts/profile.html', context)