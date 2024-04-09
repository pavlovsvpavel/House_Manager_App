from django.contrib.auth import views as auth_views, logout, login, get_user_model
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.forms import HouseManagerUserCreationForm
from django.contrib.auth import forms as auth_forms
from house_manager.accounts.mixins import OwnerRequiredMixin
from house_manager.accounts.models import Profile

UserModel = get_user_model()


class LogInUserView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_redirect_url(self):
        return reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['register_form'] = HouseManagerUserCreationForm()
        return context


class RegisterUserView(views.CreateView):
    template_name = "accounts/register.html"
    form_class = HouseManagerUserCreationForm
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_form'] = auth_forms.AuthenticationForm()
        return context

    def form_valid(self, form):
        result = super().form_valid(form)

        login(self.request, form.instance)

        return result


def logout_user(request):
    logout(request)
    return redirect('index')


class ProfileDetailsView(OwnerRequiredMixin, views.DetailView):
    queryset = Profile.objects.prefetch_related("user")
    template_name = "accounts/details_profile.html"


class ProfileUpdateView(OwnerRequiredMixin, views.UpdateView):
    MAX_IMAGE_SIZE = 1 * 1024 * 1024
    queryset = Profile.objects.all()
    template_name = "accounts/edit_profile.html"
    fields = ("first_name", "last_name", "phone_number", "profile_picture")

    def get_success_url(self):
        return reverse("details_profile", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["action_url"] = reverse_lazy("edit_profile", kwargs={'pk': self.object.pk})
        context["form_title"] = _("Edit Profile")

        return context


class ProfilePasswordChange(OwnerRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    model = UserModel

    def get_success_url(self):
        return reverse_lazy('details_profile', kwargs={'pk': self.request.user.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["action_url"] = reverse_lazy("change_password", kwargs={'pk': self.request.user.pk})
        context["form_title"] = _("Password change")

        return context


class ProfileDeleteView(OwnerRequiredMixin, views.DeleteView):
    queryset = UserModel.objects.all()
    template_name = "accounts/delete_profile.html"

    success_url = reverse_lazy("index")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        logout(request)
        user.delete()

        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return self.success_url
