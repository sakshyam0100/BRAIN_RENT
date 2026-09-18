from django import forms
from accounts.models import CustomUser

from .models import AdvisorProfile, AdvisorVerification
class AdvisorProfileForm(forms.ModelForm):

    class Meta:
        model = AdvisorProfile

        fields = [
            "bio",
            "expertise",
            "experience",
        ]

        widgets = {
            "bio": forms.Textarea(
                attrs={"rows": 5}
            ),
        }


class AdvisorVerificationForm(forms.ModelForm):

    class Meta:
        model = AdvisorVerification

        fields = [
            "government_id",
            "certificate",
            "professional_license",
        ]

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = CustomUser

        fields = [
            "profile_picture",
        ]