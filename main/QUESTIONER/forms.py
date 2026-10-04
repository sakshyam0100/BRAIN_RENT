from django import forms
from .models import QuestionerProfile
from accounts.models import CustomUser


class QuestionerProfileForm(forms.ModelForm):
    class Meta:
        model = QuestionerProfile
        fields = ['bio', 'location', 'website', 'linkedin', 'github', 'areas_of_interest']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'location': forms.TextInput(attrs={'placeholder': 'City, Country'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'linkedin': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'github': forms.URLInput(attrs={'placeholder': 'https://github.com/yourusername'}),
            'areas_of_interest': forms.TextInput(attrs={'placeholder': 'e.g., Technology, Business, Education'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+1234567890'}),
        }