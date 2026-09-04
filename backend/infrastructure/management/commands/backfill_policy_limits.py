from django.core.management.base import BaseCommand

from infrastructure.persistence.models import Policy, PolicyVersion
from infrastructure.persistence.policy_limits_data import POLICY_LIMITS


class Command(BaseCommand):
    help = "Backfill policy_limit/deductible on PolicyVersion from policy_limits_data.py."
    def handle(self, *args, **options):
        updated = 0
        for policy in Policy.objects.all():
            limits = POLICY_LIMITS.get(policy.policy_number)
            if not limits:
                self.stdout.write(self.style.WARNING(f"No limit data for '{policy.policy_number}' - skipped"))
                continue
            limit, deductible = limits
            updated += PolicyVersion.objects.filter(policy=policy).update(policy_limit=limit, deductible=deductible)
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} policy versions"))