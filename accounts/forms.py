from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


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