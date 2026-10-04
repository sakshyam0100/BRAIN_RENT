from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('notifications/mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/count/', views.notification_count, name='notification_count'),
]