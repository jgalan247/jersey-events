from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import redirect
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Event, EventStatus, EventCategory
from .forms import EventForm


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        # Only show approved events that haven't passed yet
        queryset = Event.objects.filter(
            status=EventStatus.APPROVED,
            date_time__gte=timezone.now()
        ).select_related('owner')
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category and category in dict(EventCategory.choices):
            queryset = queryset.filter(category=category)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        # Date range filtering
        date_filter = self.request.GET.get('date_filter')
        if date_filter:
            today = timezone.now()
            if date_filter == 'today':
                queryset = queryset.filter(
                    date_time__date=today.date()
                )
            elif date_filter == 'this_week':
                week_end = today + timedelta(days=7)
                queryset = queryset.filter(
                    date_time__gte=today,
                    date_time__lt=week_end
                )
            elif date_filter == 'this_month':
                month_end = today + timedelta(days=30)
                queryset = queryset.filter(
                    date_time__gte=today,
                    date_time__lt=month_end
                )
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'date')
        if sort_by == 'date':
            queryset = queryset.order_by('date_time')
        elif sort_by == 'date_desc':
            queryset = queryset.order_by('-date_time')
        elif sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'price':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = EventCategory.choices
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['date_filter'] = self.request.GET.get('date_filter', '')
        context['sort_by'] = self.request.GET.get('sort', 'date')
        
        # Maintain query parameters for pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['query_params'] = query_params.urlencode()
        
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        # Only show approved events
        return Event.objects.filter(
            status=EventStatus.APPROVED
        ).select_related('owner')


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:my_events')  # Changed back to my_events
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow CUSTOMER and ADMIN users to create events
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ['CUSTOMER', 'ADMIN']:
            messages.error(request, 'Only customers can create events.')
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.status = EventStatus.PENDING
        messages.success(
            self.request, 
            'Your event has been submitted and is pending approval.'
        )
        return super().form_valid(form)


class MyEventsView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/my_events.html'
    context_object_name = 'events'
    paginate_by = 10
    
    def get_queryset(self):
        # Show only events owned by the current user
        return Event.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add counts for different statuses
        user_events = Event.objects.filter(owner=self.request.user)
        context['pending_count'] = user_events.filter(status=EventStatus.PENDING).count()
        context['approved_count'] = user_events.filter(status=EventStatus.APPROVED).count()
        context['rejected_count'] = user_events.filter(status=EventStatus.REJECTED).count()
        return context


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:my_events')
    
    def dispatch(self, request, *args, **kwargs):
        # Get the event object
        event = self.get_object()
        
        # Check if user owns the event
        if event.owner != request.user and not request.user.is_superuser:
            messages.error(request, 'You can only edit your own events.')
            return redirect('events:my_events')
        
        # Check if event can be edited (only pending or rejected)
        if event.status == EventStatus.APPROVED:
            messages.error(request, 'Approved events cannot be edited.')
            return redirect('events:my_events')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # If event was rejected, change back to pending when edited
        if form.instance.status == EventStatus.REJECTED:
            form.instance.status = EventStatus.PENDING
            messages.success(
                self.request, 
                'Your event has been updated and resubmitted for approval.'
            )
        else:
            messages.success(self.request, 'Your event has been updated.')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('events:my_events')
    
    def dispatch(self, request, *args, **kwargs):
        # Get the event object
        event = self.get_object()
        
        # Check if user owns the event
        if event.owner != request.user and not request.user.is_superuser:
            messages.error(request, 'You can only delete your own events.')
            return redirect('events:my_events')
        
        # Optionally: prevent deletion of approved events
        # if event.status == EventStatus.APPROVED:
        #     messages.error(request, 'Approved events cannot be deleted.')
        #     return redirect('events:my_events')
        
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Your event has been deleted.')
        return super().delete(request, *args, **kwargs)