from django.core.management.base import BaseCommand

from infrastructure.persistence.models import Claim, Client, PolicyVersion, User


class Command(BaseCommand):
    help = "Create a test claim against a real ingested policy version."

    def add_arguments(self, parser):
        parser.add_argument("--policy-code", default="auto_comp")
        parser.add_argument("--claim-date", default="2024-06-15")

    def handle(self, *args, **options):
        client, _ = Client.objects.get_or_create(name="Default Synthetic Client")
        adjuster, _ = User.objects.get_or_create(username="test_adjuster", defaults={"role": "ADJUSTER"})
        pv = PolicyVersion.objects.filter(policy__policy_number=options["policy_code"]).order_by("effective_from").first()
        if not pv:
            self.stdout.write(self.style.ERROR(f"No policy version found for code {options['policy_code']}"))
            return
        claim = Claim.objects.create(
            client=client, policy_version=pv, adjuster=adjuster, claim_date=options["claim_date"], status="submitted",
        )
        self.stdout.write(self.style.SUCCESS(f"Created claim {claim.id} against {pv.version} ({pv.policy.policy_number})"))