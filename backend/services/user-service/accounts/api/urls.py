"""
API URL ROUTES FOR USER SERVICE
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # AUTHENTICATION
    path('auth/register/', views.RegisterView.as_view(), name='auth_register'),
    path('auth/login/', views.LoginView.as_view(), name='auth_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth_refresh'),
    path('auth/verify-otp/', views.VerifyOTPView.as_view(), name='auth_verify_otp'),
    path('auth/resend-otp/', views.ResendOTPView.as_view(), name='auth_resend_otp'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='auth_change_password'),
    
    # USER PROFILE
    path('users/me/', views.UserProfileView.as_view(), name='user_profile'),
    path('users/me/', views.UpdateUserProfileView.as_view(), name='user_profile_update'),
    
    # ADMIN
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<uuid:id>/', views.UserDetailView.as_view(), name='user_detail'),
]
