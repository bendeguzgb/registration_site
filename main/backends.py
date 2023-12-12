from http import HTTPStatus

import requests
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied

from . import settings
from .models import User, UserType


def get_profile_by_orcid_id(orcid, token):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    url = f"{settings.ORCID_API_URL}{orcid}/record"

    return requests.get(url, headers=headers).json()


def get_orcid_user_auth_data(token):
    headers = {"Accept": "application/json"}
    request_body = {
        "client_id": settings.ORCID_CLIENT_ID,
        "client_secret": settings.ORCID_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": token,
        "redirect_uri": settings.REDIRECT_URL
    }

    response = requests.post(settings.ORCID_OAUTH_URL, headers=headers, data=request_body)

    if response.status_code == HTTPStatus.OK:
        return response.json()
    else:
        raise PermissionDenied()


class OrcidBackend(BaseBackend):
    def authenticate(self, request, token=None, *args, **kwargs):
        if token is None:
            return None

        user_auth_data = get_orcid_user_auth_data(token)

        if user_auth_data.get("error") is not None or user_auth_data.get("orcid") is None:
            raise PermissionDenied()

        orcid_id = user_auth_data.get("orcid")
        access_token = user_auth_data.get("access_token")

        profile = get_profile_by_orcid_id(orcid_id, access_token)
        first_name = profile.get("person").get("name").get("given-names").get("value")
        last_name = profile.get("person").get("name").get("family-name").get("value")
        emails = profile.get("person").get("emails").get("email")
        # I may have missed it, but I didn't see a phone number field
        # phone_number = profiel.get
        primary_mail = ""

        if emails is None or not emails:
            print(f"Error! Could not retrieve any email from ORCID!")
            raise PermissionDenied()

        for email in emails:
            if email.get("email") is not None and email.get("primary") is True:
                primary_mail = email.get("email")

        try:
            user = User.objects.get(orcid_id=orcid_id)

            if user.email != primary_mail:
                user.email = primary_mail

            if user.first_name != first_name:
                user.first_name = first_name

            if user.last_name != last_name:
                user.last_name = last_name

            user.save()

        except User.DoesNotExist:
            user = User(orcid_id=orcid_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=primary_mail,
                        user_type=UserType.VISITOR)
            user.set_unusable_password()
            user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
