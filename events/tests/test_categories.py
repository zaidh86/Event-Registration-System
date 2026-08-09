from django.urls import reverse

from common.testing import APITestCase


class CategoryListTests(APITestCase):
    url = reverse("categories-list")

    def test_lists_seeded_categories_publicly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["count"], 0)
        for item in response.data["results"]:
            self.assertEqual(set(item), {"id", "name"})
        self.assertIn("Technology", [item["name"] for item in response.data["results"]])

    def test_orders_categories_by_name(self):
        response = self.client.get(self.url)

        names = [item["name"] for item in response.data["results"]]
        self.assertEqual(names, sorted(names))
