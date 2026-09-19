from django import forms
from django.core.exceptions import ValidationError

from .models import Review


class ReviewForm(forms.ModelForm):

    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ - Excellent'),
        (4, '⭐⭐⭐⭐ - Very Good'),
        (3, '⭐⭐⭐ - Good'),
        (2, '⭐⭐ - Fair'),
        (1, '⭐ - Poor'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-rating'}),
        initial=5
    )

    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 5,
                'placeholder': 'Share your experience with this advisor...',
                'class': 'form-control'
            }
        ),
        required=False,
        max_length=1000,
        help_text='Optional: Add comments about your experience (max 1000 characters)'
    )

    class Meta:

        model = Review

        fields = [
            "rating",
            "comment",
        ]

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                raise ValidationError('Rating must be between 1 and 5.')
            return rating_int
        except (ValueError, TypeError):
            raise ValidationError('Please select a valid rating.')

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        if comment and len(comment) > 1000:
            raise ValidationError('Comment cannot exceed 1000 characters.')
        return comment