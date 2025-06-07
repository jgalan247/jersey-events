from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class EventCategory(models.TextChoices):
    THINGS_TO_DO = 'THINGS_TO_DO', 'Things to Do'
    FOOD_DRINK = 'FOOD_DRINK', 'Food & Drink'
    ART_CULTURE = 'ART_CULTURE', 'Art & Culture'
    THEATRE_FILMS = 'THEATRE_FILMS', 'Theatre & Films'


class EventStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'


class Event(models.Model):
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=EventCategory.choices,
        default=EventCategory.THINGS_TO_DO
    )
    
    # Date and Location
    date_time = models.DateTimeField()
    location = models.CharField(max_length=300)
    
    # Pricing and Capacity
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price in GBP'
    )
    capacity = models.PositiveIntegerField(
        help_text='Maximum number of attendees'
    )
    
    # Image
    image = models.ImageField(
        upload_to='events/images/',
        blank=True,
        null=True
    )
    
    # Status and Ownership
    status = models.CharField(
        max_length=10,
        choices=EventStatus.choices,
        default=EventStatus.PENDING
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date_time']
        indexes = [
            models.Index(fields=['status', 'date_time']),
            models.Index(fields=['category']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_upcoming(self):
        """Check if the event is in the future"""
        return self.date_time > timezone.now()
    
    @property
    def available_tickets(self):
        """Calculate available tickets"""
        from tickets.models import Ticket  # Import here to avoid circular import
        
        # Count sold tickets for this event
        sold_tickets = Ticket.objects.filter(
            event=self,
            order__status='COMPLETED'
        ).aggregate(
            total_sold=models.Sum('quantity')
        )['total_sold'] or 0
        
        return self.capacity - sold_tickets
    
    def can_edit(self, user):
        """Check if user can edit this event"""
        return user == self.owner or user.is_superuser
    
    def can_delete(self, user):
        """Check if user can delete this event"""
        return user == self.owner or user.is_superuser