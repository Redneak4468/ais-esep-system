from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.views.generic import CreateView, DetailView, ListView
from .forms import SignUpForm
from .models import Profile


class SignUpView(CreateView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        # автоматически логиним свежесозданного пользователя
        login(self.request, self.object)
        return response


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "accounts/dashboard.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        return self.request.user.profile
