from django.contrib import admin
from .models import Question,QuestionAssignment,Category
# Register your models here.
admin.site.register(Question)
admin.site.register(QuestionAssignment)
admin.site.register(Category)