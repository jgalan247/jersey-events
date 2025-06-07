from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Event, EventCategory


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'category',
            'date_time',
            'location',
            'price',
            'capacity',
            'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'date_time': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                }
            ),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'date_time': 'Date & Time',
            'price': 'Price (£)',
            'capacity': 'Maximum Capacity',
        }
        help_texts = {
            'price': 'Enter 0 for free events',
            'capacity': 'Maximum number of attendees',
            'image': 'Optional. Recommended size: 800x400 pixels'
        }
    
    def clean_date_time(self):
        date_time = self.cleaned_data.get('date_time')
        if date_time and date_time <= timezone.now():
            raise ValidationError('Event date must be in the future.')
        return date_time
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Limit file size to 5MB
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large ( > 5MB )')
            # Validate file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            import os
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Unsupported file extension. Use: jpg, jpeg, png, or gif')
        return image