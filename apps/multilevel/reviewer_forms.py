"""
Custom forms for Reviewer admin
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

User = get_user_model()


class ReviewerCreationForm(UserCreationForm):
    """
    Custom form for creating new reviewers
    Includes phone, name, and password fields
    """
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Telefon raqami',
        help_text='Masalan: +998901234567',
        widget=forms.TextInput(attrs={'placeholder': '+998901234567'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Ism',
        widget=forms.TextInput(attrs={'placeholder': 'Ali'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Familiya',
        widget=forms.TextInput(attrs={'placeholder': 'Valiyev'})
    )
    email = forms.EmailField(
        required=False,
        label='Email',
        help_text='Ixtiyoriy',
        widget=forms.EmailInput(attrs={'placeholder': 'ali@example.com'})
    )
    
    class Meta:
        model = User
        fields = ('phone', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password validators - no validation required
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = 'Yuqoridagi parolni takrorlang'
        if hasattr(self.fields['password1'], 'validators'):
            self.fields['password1'].validators = []
        if hasattr(self.fields['password2'], 'validators'):
            self.fields['password2'].validators = []
    
    def clean_phone(self):
        """Validate phone number is unique"""
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('Bu telefon raqami allaqachon mavjud!')
        return phone
    
    def _post_clean(self):
        """Override to skip password validation"""
        super(UserCreationForm, self)._post_clean()
        # Get passwords
        password = self.cleaned_data.get('password2')
        if password:
            # Set password without validation
            self.instance.password = password
    
    def save(self, commit=True):
        """Save user and add to Reviewer group"""
        user = super().save(commit=False)
        user.is_active = True
        user.is_staff = False  # Reviewers are NOT staff
        user.is_superuser = False
        
        if commit:
            user.save()
            
            # Add to Reviewer group
            try:
                reviewer_group = Group.objects.get(name='Reviewer')
                user.groups.add(reviewer_group)
            except Group.DoesNotExist:
                pass  # Group will be created by setup_reviewers command
        
        return user


class ReviewerChangeForm(UserChangeForm):
    """
    Custom form for editing reviewers
    """
    class Meta:
        model = User
        fields = ('phone', 'first_name', 'last_name', 'email', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password field from change form
        if 'password' in self.fields:
            del self.fields['password']

