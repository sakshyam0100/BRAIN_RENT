from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'advisor', 'questioner', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'payment_method', 'created_at']
    search_fields = ['question__title', 'advisor__user__username', 'questioner__username', 'khalti_txn_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('question', 'advisor', 'questioner', 'amount', 'currency', 'status')
        }),
        ('Khalti Details', {
            'fields': ('khalti_txn_id', 'khalti_idx', 'payment_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
