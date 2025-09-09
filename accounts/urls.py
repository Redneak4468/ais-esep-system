from django.urls import path
from .views import SignUpView, ProfileDetailView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("my-profile/", ProfileDetailView.as_view(), name="profile_detail"),
]