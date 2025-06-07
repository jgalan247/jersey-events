from django.contrib import admin
from django.utils.html import format_html
from .models import Order, Ticket, Cart, CartItem


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ['ticket_id', 'total_price', 'is_used', 'used_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'status_badge', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    inlines = [TicketInline]
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#FFA500',
            'COMPLETED': '#28A745',
            'CANCELLED': '#DC3545',
            'REFUNDED': '#6C757D'
        }
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; '
            'border-radius: 3px; color: white;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'event', 'attendee_name', 'quantity', 'is_used', 'created_at']
    list_filter = ['is_used', 'event', 'created_at']
    search_fields = ['ticket_id', 'attendee_name', 'attendee_email', 'event__title']
    readonly_fields = ['ticket_id', 'total_price', 'created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('event', 'order', 'order__user')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_amount', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'total_amount', 'total_items']
    inlines = [CartItemInline]