from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email_on_successful_registration(user):
    html_message = render_to_string(
        "accounts/greeting_email.html",
        {"user": user}
    )

    plain_message = strip_tags(html_message)

    send_mail(
        subject="Successful registration at House Manager",
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=(user.email,),
    )
