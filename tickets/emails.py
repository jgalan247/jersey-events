from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings


def send_order_confirmation(request, order):
    """Send order confirmation email"""
    # Get current site domain
    current_site = get_current_site(request)
    domain = f"http://{current_site.domain}"
    
    # Email context
    context = {
        'order': order,
        'domain': domain,
    }
    
    # Render email templates
    subject = f'[Jersey Events] Order Confirmation - #{order.order_id}'
    text_content = render_to_string('emails/order_confirmation.txt', context)
    html_content = render_to_string('emails/order_confirmation.html', context)
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email],
    )
    email.attach_alternative(html_content, "text/html")
    
    # Send email
    email.send()


def send_event_reminder(ticket, hours_before=24):
    """Send event reminder email"""
    event = ticket.event
    
    context = {
        'ticket': ticket,
        'event': event,
        'hours_before': hours_before,
    }
    
    subject = f'[Jersey Events] Reminder: {event.title} - Tomorrow!'
    text_content = render_to_string('emails/event_reminder.txt', context)
    html_content = render_to_string('emails/event_reminder.html', context)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[ticket.attendee_email],
    )
    email.attach_alternative(html_content, "text/html")
    
    email.send()