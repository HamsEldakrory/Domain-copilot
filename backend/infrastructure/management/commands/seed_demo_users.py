from django.core.management.base import BaseCommand

from infrastructure.persistence.models import User


class Command(BaseCommand):
    help = "Create seeded demo accounts for README/demo purposes."

    def handle(self, *args, **options):
        adjuster, created_a = User.objects.get_or_create(
            username="demo_adjuster", defaults={"role": "ADJUSTER"},
        )
        if created_a:
            adjuster.set_password("DemoPass123!")
            adjuster.save()

        manager, created_m = User.objects.get_or_create(
            username="demo_manager", defaults={"role": "MANAGER"},
        )
        if created_m:
            manager.set_password("DemoPass123!")
            manager.save()

        self.stdout.write(self.style.SUCCESS(
            "Seeded: demo_adjuster / demo_manager (password: DemoPass123!)"
        ))