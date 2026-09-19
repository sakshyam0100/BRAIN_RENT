from django import forms

from .models import Question
from .models import Answer


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question

        fields = [
            "category",
            "title",
            "description",
        ]

        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Describe your question clearly..."
                }
            ),
        }

class AnswerForm(forms.ModelForm):

    class Meta:

        model = Answer

        fields = [
            "content",
        ]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 8,
                    "placeholder": "Write your official answer here..."
                }
            )
        }