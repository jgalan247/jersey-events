from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Event, EventStatus


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'date_time',
        'location',
        'price',
        'status_badge',
        'owner',
        'created_at'
    ]
    list_filter = [
        'status',
        'category',
        'date_time',
        'created_at'
    ]
    search_fields = [
        'title',
        'description',
        'location',
        'owner__email',
        'owner__first_name',
        'owner__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_time'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'category', 'image')
        }),
        ('Schedule & Location', {
            'fields': ('date_time', 'location')
        }),
        ('Pricing & Capacity', {
            'fields': ('price', 'capacity')
        }),
        ('Status & Ownership', {
            'fields': ('status', 'owner')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            EventStatus.PENDING: '#FFA500',
            EventStatus.APPROVED: '#28A745',
            EventStatus.REJECTED: '#DC3545'
        }
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; '
            'border-radius: 3px; color: white;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Optimize queries
        return qs.select_related('owner')
    
    actions = ['approve_events', 'reject_events']
    
    def approve_events(self, request, queryset):
        updated = queryset.update(status=EventStatus.APPROVED)
        self.message_user(request, f'{updated} events approved.')
    approve_events.short_description = 'Approve selected events'
    
    def reject_events(self, request, queryset):
        updated = queryset.update(status=EventStatus.REJECTED)
        self.message_user(request, f'{updated} events rejected.')
    reject_events.short_description = 'Reject selected events'