from house_manager.accounts.models import UserProfile


class GetProfileMixin:

    @staticmethod
    def get_profile():
        return UserProfile.objects.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = self.get_profile()

        if profile is None:
            context["profile"] = False

        else:
            context["profile"] = True

        return context