from django.contrib import admin
from QUESTIONER.models import Questioner
# Register your models here.
@admin.register(Questioner)
class Questioneradmin(admin.ModelAdmin):
    list_display = ['name','email']
    search_fields =['name','phone']
