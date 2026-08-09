"""Shared test infrastructure."""

from django.core.cache import cache
from rest_framework import test


class APITestCase(test.APITestCase):
    def setUp(self):
        super().setUp()
        # Throttle counters live in the cache and would otherwise leak
        # between test methods.
        cache.clear()

    def assertErrorEnvelope(self, response, code=None):
        self.assertIn("error", response.data)
        error = response.data["error"]
        self.assertEqual(set(error), {"code", "message", "details"})
        if code is not None:
            self.assertEqual(error["code"], code)
