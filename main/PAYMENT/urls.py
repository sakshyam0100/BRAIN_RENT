from django.urls import path
from . import views

urlpatterns = [
    path('initiate/<int:question_id>/', views.initiate_payment, name='initiate_payment'),
    path('callback/<int:payment_id>/', views.payment_callback, name='payment_callback'),
    path('return/<int:payment_id>/', views.payment_return, name='payment_return'),
    path('history/', views.payment_history, name='payment_history'),
    path('detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
]