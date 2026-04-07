from django.db import models

# Create your models here.
class Questioner(models.Model):
    name = models.CharField(max_length=255,unique='True')
    email = models.EmailField(unique=True)
    phone = models.PositiveBigIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    total_questions = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
       return self.name