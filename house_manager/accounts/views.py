from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import views as auth_views, logout, get_user_model, update_session_auth_hash
from django.core.cache import cache
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from allauth.account.models import EmailAddress

from house_manager.accounts.forms import HouseManagerUserCreationForm, HouseManagerUserSetPasswordForm, \
    HouseManagerUserLoginForm
from house_manager.accounts.mixins import OwnerRequiredMixin
from house_manager.accounts.models import Profile

UserModel = get_user_model()


class LogInUserView(auth_views.LoginView):
    template_name = "accounts/login.html"
    form_class = HouseManagerUserLoginForm
    redirect_authenticated_user = True

    # Security #11: the login form must not be usable to flood someone's
    # inbox — a fresh confirmation mail goes out at most once per interval.
    VERIFICATION_RESEND_COOLDOWN = timedelta(minutes=5)

    def get_redirect_url(self):
        return reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['register_form'] = HouseManagerUserCreationForm()
        context['login_form'] = context.pop('form')

        return context

    def form_valid(self, form):
        user = form.get_user()
        email_address = EmailAddress.objects.filter(user=user).first()
        if email_address and not email_address.verified:
            # The confirmation key is an HMAC token (no DB rows), so the
            # resend cooldown lives in the cache: the login form cannot be
            # used to flood someone's inbox.
            cooldown_key = f"verification-sent:{user.pk}"
            if not cache.get(cooldown_key):
                email_address.send_confirmation(self.request)
                cache.set(
                    cooldown_key,
                    True,
                    self.VERIFICATION_RESEND_COOLDOWN.total_seconds(),
                )
            return redirect("account_email_verification_sent")
        return super().form_valid(form)


class RegisterUserView(views.CreateView):
    template_name = "accounts/register.html"
    form_class = HouseManagerUserCreationForm
    success_url = reverse_lazy("index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['register_form'] = context.pop('form')
        context['login_form'] = HouseManagerUserLoginForm()

        return context

    def form_valid(self, form):
        result = super().form_valid(form)
        user = form.instance

        user.has_set_password = True
        user.save()

        # Security #11: the account starts unverified. allauth emails the
        # confirmation link; the login happens through that link (and the
        # login view refuses unverified accounts) — no immediate login.
        email_address = EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=False,
        )
        email_address.send_confirmation(self.request)

        return redirect("account_email_verification_sent")


def logout_user(request):
    # Security #10: a GET link can log the user out from any third-party
    # page; logout is POST-only now. Stale profile-menu links that somehow
    # GET the URL just land back on the index, logged in.
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    storage = messages.get_messages(request)
    for message in storage:
        pass
    return redirect('index')



class ProfileDetailsView(OwnerRequiredMixin, views.DetailView):
    queryset = Profile.objects.select_related("user")
    template_name = "accounts/details_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class ProfileUpdateView(OwnerRequiredMixin, views.UpdateView):
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

    def form_valid(self, form):
        # The queryset is UserModel: the fetched object IS the user row and
        # deleting it cascades to the Profile. Log out first so the session
        # does not outlive the account. (A custom delete() override would
        # never run: Django's DeleteView POSTs through the form flow -
        # post() -> form_valid() -> object.delete().)
        logout(self.request)
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url

class ProfilePasswordSet(OwnerRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'accounts/password_set.html'
    form_class = HouseManagerUserSetPasswordForm

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.has_set_password = True
        self.request.user.save()
        update_session_auth_hash(self.request, form.user)
        return response

    def get_success_url(self):
        return reverse_lazy('details_profile', kwargs={'pk': self.request.user.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = reverse_lazy("set_password", kwargs={'pk': self.request.user.pk})
        context["form_title"] = _("Set Password")
        return context