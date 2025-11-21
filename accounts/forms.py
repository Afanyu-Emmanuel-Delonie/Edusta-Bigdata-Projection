"""
Forms for the Accounts app
Uses Django's built-in authentication forms with custom styling
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginForm(AuthenticationForm):
    """
    Custom login form with Tailwind CSS styling
    Extends Django's built-in AuthenticationForm for security
    """
    
    # Username field (can be email or username)
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'w-full mt-2 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#689ada] focus:border-transparent outline-none transition',
            'placeholder': 'Enter your User Name',
            'autocomplete': 'username',
        }),
        label='User Name'
    )
    
    # Password field
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full mt-2 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#689ada] focus:border-transparent outline-none transition',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
        label='Password'
    )
    
    # Remember me checkbox (optional)
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-auca-blue border-gray-300 rounded focus:ring-auca-blue',
        }),
        label='Remember me'
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form and remove default help text
        """
        super().__init__(*args, **kwargs)
        # Remove default help text for cleaner UI
        for field in self.fields.values():
            field.help_text = None