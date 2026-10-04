from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, CustomTokenObtainPairView, ProfileView,
    CategoryListView, CategoryDetailView,
    QuestionViewSet, AdvisorViewSet, AssignmentViewSet,
    ConversationViewSet, ReviewViewSet, PaymentViewSet
)

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'advisors', AdvisorViewSet, basename='advisor')
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='api_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='api_profile'),

    # Categories
    path('categories/', CategoryListView.as_view(), name='api_categories'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='api_category_detail'),

    # ViewSets (with router)
    path('', include(router.urls)),
]
