from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.test_users import make_user
from apps.tenants.models import Tenant


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.north = Tenant.objects.create(name="North", slug="north")
        self.south = Tenant.objects.create(name="South", slug="south")
        self.member = make_user("member1", role="accountant", tenant=self.north)
        self.nonmember = make_user("nonmember1", role="accountant")

    def test_member_list_and_detail_are_scoped(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("tenant-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in response.json()["results"]], [str(self.north.pk)]
        )
        self.assertEqual(
            self.client.get(reverse("tenant-detail", args=[self.north.pk])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("tenant-detail", args=[self.south.pk])).status_code,
            404,
        )

    def test_nonmember_and_roleless_user_cannot_see_tenant(self):
        self.client.force_login(self.nonmember)
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])
        self.assertEqual(
            self.client.get(reverse("tenant-detail", args=[self.north.pk])).status_code,
            404,
        )
        roleless = make_user("roleless1", tenant=self.north)
        self.client.force_login(roleless)
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])

    def test_expired_membership_and_inactive_tenant_are_hidden(self):
        self.client.force_login(self.member)
        membership = self.member.tenant_memberships.get(tenant=self.north)
        membership.effective_until = timezone.now()
        membership.save()
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])
        membership.effective_until = None
        membership.save()
        self.north.is_active = False
        self.north.save()
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])

    def test_no_generic_tenant_mutation_routes(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(reverse("tenant-list"), {}).status_code, 405)
        self.assertEqual(
            self.client.delete(
                reverse("tenant-detail", args=[self.north.pk])
            ).status_code,
            405,
        )
