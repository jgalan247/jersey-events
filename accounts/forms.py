from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpForm(UserCreationForm):
    """Registration form with role selection."""
    
    email = forms.EmailField(
        max_length=254,
        help_text='Required. Enter a valid email address.'
    )
    
    role = forms.ChoiceField(
        choices=[
            (User.Role.USER, 'User - Browse and buy tickets'),
            (User.Role.CUSTOMER, 'Customer - List events'),
        ],
        help_text='Select your account type.'
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'role')


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'first_name', 'last_name', 'role')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'