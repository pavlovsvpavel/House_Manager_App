from django.contrib.auth import views as auth_views, logout, login, get_user_model
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views import generic as views

from house_manager.accounts.forms import HouseManagerUserCreationForm
from django.contrib.auth import forms as auth_forms
from house_manager.accounts.mixins import OwnerRequiredMixin
from house_manager.accounts.models import Profile

UserModel = get_user_model()


class LogInUserView(OwnerRequiredMixin, auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['register_form'] = HouseManagerUserCreationForm()
        return context


class RegisterUserView(OwnerRequiredMixin, views.CreateView):
    template_name = "accounts/register.html"
    form_class = HouseManagerUserCreationForm
    success_url = reverse_lazy("index")

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
    queryset = Profile.objects.prefetch_related("user").all()
    template_name = "accounts/details_profile.html"


class ProfileUpdateView(OwnerRequiredMixin, views.UpdateView):
    queryset = Profile.objects.all()
    template_name = "accounts/edit_profile.html"
    fields = ("first_name", "last_name", "phone_number", "profile_picture")

    def get_success_url(self):
        return reverse("details_profile", kwargs={
            "pk": self.object.pk,
        })


class ProfilePasswordChange(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    model = UserModel

    def get_success_url(self):
        return reverse_lazy('details_profile', kwargs={'pk': self.request.user.pk})


class ProfileDeleteView(OwnerRequiredMixin, views.DeleteView):
    queryset = UserModel.objects.all()
    template_name = "accounts/delete_profile.html"

    success_url = reverse_lazy("index")

    # TODO: Add confirmation with password
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        logout(request)
        user.delete()

        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return self.success_url
