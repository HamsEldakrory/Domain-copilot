from django.core.management.base import BaseCommand
from infrastructure.persistence.models import Policy, PolicyVersion

LIMITS = {
    "auto_comp": (30000, 500),
    "home_std": (250000, 1000),
    "health_p": (25000, 250),
    "rent_std": (25000, 250),
    "life_term": (100000, 0),
    "travel_basic": (15000, 100),
    "biz_liab": (500000, 2500),
    "marine_cargo": (75000, 1000),
    "pet_care": (10000, 100),
    "cyber_sme": (200000, 5000),
}

class Command(BaseCommand):
    help = "Backfill policy_limit/deductible on PolicyVersion from known synthetic corpus values."
    def handle(self, *args, **options):
        updated = 0
        for policy in Policy.objects.all():
            limits = LIMITS.get(policy.policy_number)
            if not limits:
                continue
            limit, deductible = limits
            updated += PolicyVersion.objects.filter(policy=policy).update(
                policy_limit=limit, deductible=deductible
            )
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} policy versions"))