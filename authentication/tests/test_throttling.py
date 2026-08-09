from unittest.mock import patch

from django.urls import reverse
from rest_framework.throttling import ScopedRateThrottle

from common.testing import APITestCase


class AuthThrottlingTests(APITestCase):
    url = reverse("auth-login")

    # DRF binds THROTTLE_RATES to the throttle class at import time, so the
    # rate must be patched on the class; override_settings has no effect.
    @patch.dict(ScopedRateThrottle.THROTTLE_RATES, {"auth": "3/minute"})
    def test_auth_scope_throttles_after_limit(self):
        payload = {"email": "nobody@example.com", "password": "irrelevant"}

        for _ in range(3):
            response = self.client.post(self.url, payload)
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 429)
        self.assertErrorEnvelope(response, code="throttled")
        self.assertIn("wait_seconds", response.data["error"]["details"])
