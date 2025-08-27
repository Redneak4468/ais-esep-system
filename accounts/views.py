from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.views.generic import CreateView

from .forms import SignUpForm

class SignUpView(CreateView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        # автоматически логиним свежесозданного пользователя
        login(self.request, self.object)
        return response