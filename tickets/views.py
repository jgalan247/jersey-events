from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse  
from django.db import transaction
from decimal import Decimal
import stripe
from django.conf import settings
from events.models import Event
from .models import Cart, CartItem, Order, Ticket
import qrcode
from io import BytesIO

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def add_to_cart(request, event_id):
    """Add tickets to cart"""
    event = get_object_or_404(Event, pk=event_id, status='APPROVED')
    quantity = int(request.POST.get('quantity', 1))
    
    # Validate quantity
    if quantity < 1:
        messages.error(request, 'Invalid quantity.')
        return redirect('events:event_detail', pk=event_id)
    
    if quantity > event.available_tickets:
        messages.error(request, f'Only {event.available_tickets} tickets available.')
        return redirect('events:event_detail', pk=event_id)
    
    # Get or create cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        event=event,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Update quantity if item already in cart
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{quantity} ticket(s) added to cart.')
    return redirect('tickets:cart')


@login_required
def view_cart(request):
    """Display shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'tickets/cart.html', context)


@login_required
def update_cart_item(request, item_id):
    """Update quantity of cart item"""
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    else:
        if quantity > cart_item.event.available_tickets:
            messages.error(request, f'Only {cart_item.event.available_tickets} tickets available.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated.')
    
    return redirect('tickets:cart')


@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('tickets:cart')


@login_required
def checkout(request):
    """Process checkout"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('tickets:cart')
    
    if request.method == 'POST':
        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.total_amount,
                status='PENDING'
            )
            
            # Create tickets for each cart item
            for item in cart.items.all():
                # Check availability one more time
                if item.quantity > item.event.available_tickets:
                    messages.error(request, f'Not enough tickets for {item.event.title}')
                    order.delete()
                    return redirect('tickets:cart')
                
                Ticket.objects.create(
                    order=order,
                    event=item.event,
                    attendee_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                    attendee_email=request.user.email,
                    quantity=item.quantity,
                    unit_price=item.event.price
                )
            
            # Create Stripe payment intent
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(order.total_amount * 100),  # Stripe uses cents
                    currency='gbp',
                    metadata={
                        'order_id': str(order.order_id),
                        'user_id': request.user.id
                    }
                )
                order.stripe_payment_intent = intent.id
                order.save()
                
                # Clear cart after creating order
                cart.items.all().delete()
                
                return render(request, 'tickets/checkout.html', {
                    'order': order,
                    'client_secret': intent.client_secret,
                    'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                })
                
            except stripe.error.StripeError as e:
                messages.error(request, f'Payment error: {str(e)}')
                order.delete()
                return redirect('tickets:cart')
    
    return redirect('tickets:cart')


@login_required
def payment_success(request, order_id):
    """Handle successful payment"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Update order status
    order.status = 'COMPLETED'
    order.save()
    
    messages.success(request, 'Payment successful! Your tickets have been confirmed.')
    return render(request, 'tickets/payment_success.html', {'order': order})


@login_required
def my_orders(request):
    """Display user's orders"""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'tickets/my_orders.html', {'orders': orders})

@login_required
def ticket_qr_code(request, ticket_id):
    """Generate QR code for a ticket"""
    ticket = get_object_or_404(
        Ticket, 
        ticket_id=ticket_id,
        order__user=request.user,
        order__status='COMPLETED'
    )
    
    # Create QR code data
    qr_data = f"TICKET:{ticket.ticket_id}\nEVENT:{ticket.event.title}\nDATE:{ticket.event.date_time}\nQTY:{ticket.quantity}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Return image response
    return HttpResponse(buffer, content_type='image/png')

@login_required
def ticket_qr_code(request, ticket_id):
    """Generate QR code for a ticket"""
    ticket = get_object_or_404(
        Ticket, 
        ticket_id=ticket_id,
        order__user=request.user,
        order__status='COMPLETED'
    )
    
    # Create URL for ticket validation
    # In production, use your actual domain
    domain = request.get_host()
    validation_url = f"http://{domain}/tickets/validate/{ticket.ticket_id}/"
    
    # Generate QR code with URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(validation_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Return image response
    return HttpResponse(buffer, content_type='image/png')