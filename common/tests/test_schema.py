from django.urls import reverse

from common.testing import APITestCase


class ApiDocumentationTests(APITestCase):
    def test_openapi_schema_is_publicly_available(self):
        response = self.client.get(reverse("schema"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"openapi", response.content)
        self.assertIn(b"/api/v1/events/", response.content)
        self.assertIn(b"/api/v1/organizer/dashboard/", response.content)

    def test_swagger_ui_is_publicly_available(self):
        response = self.client.get(reverse("docs"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"swagger", response.content.lower())
