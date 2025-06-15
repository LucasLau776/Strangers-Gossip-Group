from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Post, Comment, UserProfile

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'post', 'parent', 'content', 'image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*,.gif'})
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content:
            raise forms.ValidationError("Content cannot be empty")
        return content

class MMUAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    error_messages = {
        'invalid_login': "Invalid username or password. Please try again.",
        'inactive': "This account is inactive.",
    }

class MMURegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Your MMU email (@student.mmu.edu.my or @mmu.edu.my)',
            'class': 'form-control'
        }),
        help_text="Must register with MMU student or faculty/staff email address"
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Username', 
            'class': 'form-control'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        allowed_domains = ['@student.mmu.edu.my', '@mmu.edu.my']
        
        if not any(email.endswith(domain) for domain in allowed_domains):
            raise ValidationError(
                'Only MMU institutional emails are allowed. '
                'Please use your @student.mmu.edu.my or @mmu.edu.my email.'
            )
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar',]
        
    new_username = forms.CharField(
        required=False,
        max_length=150,
        help_text="You can change username once every 30 days"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.userprofile.can_change_username():
            self.fields['new_username'].initial = self.user.username

class CustomPasswordChangeForm(PasswordChangeForm):
    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            profile = user.userprofile
            profile.last_password_change = timezone.now()
            profile.save()
        return user
