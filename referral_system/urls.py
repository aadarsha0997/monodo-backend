from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    AgentCreationView,
    AgentListView,
    AgentDetailView,
    MyReferralsView,
    ReferralTrackingListView,
    DashboardStatsView,
    ValidateReferralCodeView,
    UserRecordImagesView
)

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Agent Management (SuperAdmin only)
    path('agents/create/', AgentCreationView.as_view(), name='agent-create'),
    path('agents/', AgentListView.as_view(), name='agent-list'),
    path('agents/<uuid:agent_id>/', AgentDetailView.as_view(), name='agent-detail'),
    
    # Referrals
    path('my-referrals/', MyReferralsView.as_view(), name='my-referrals'),
    path('referral-tracking/', ReferralTrackingListView.as_view(), name='referral-tracking'),
    path('validate-referral-code/', ValidateReferralCodeView.as_view(), name='validate-referral-code'),
    
    # Dashboard
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),

    # Record images
    path('records/images/', UserRecordImagesView.as_view(), name='user-record-images'),
]