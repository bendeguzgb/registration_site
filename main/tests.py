from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

DENIED_NOT_FOUNT_TEXT = "The page you are trying to access does not exist, or you do not have permission to view it."


class PagePermissionTest(TestCase):
    def test_page_contains_denied_message(self):
        url = reverse("main:admin_list_users")
        response: HttpResponse = self.client.get(url)

        self.assertContains(response, DENIED_NOT_FOUNT_TEXT, status_code=404)

    def test_public_page(self):
        page_names = ["home", "login", "visitor_register", "client_register"]

        for page_name in page_names:
            url = reverse(f"main:{page_name}")
            response: HttpResponse = self.client.get(url)

            self.assertNotContains(response, DENIED_NOT_FOUNT_TEXT, status_code=200)
