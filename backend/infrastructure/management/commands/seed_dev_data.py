"""
Idempotent comprehensive dev seed.

Creates:
  - 2 managers: demo_manager, mgr_sarah
  - 4 adjusters: demo_adjuster, adj_carlos, adj_priya, test_adjuster
  - 5 clients: Acme Corp, Riverside Holdings, Pinnacle Financial, Global Tech Systems, Apex Logistics
  - 10 distinct policy types (Cyber, Auto, Home, Health, Renters, Life, Travel, Business, Cargo, Pet)
  - Diverse claims covering a rich variety of policies, clients, adjusters, and statuses

Run: python manage.py seed_dev_data
"""
from datetime import date
from django.core.management.base import BaseCommand
from infrastructure.persistence.models import Client, Claim, Policy, PolicyVersion, User


MANAGERS = [
    {"username": "demo_manager", "role": "MANAGER", "password": "DemoPass123!"},
    {"username": "mgr_sarah",    "role": "MANAGER", "password": "DemoPass123!"},
]

ADJUSTERS = [
    {"username": "demo_adjuster", "role": "ADJUSTER", "password": "DemoPass123!"},
    {"username": "adj_carlos",    "role": "ADJUSTER", "password": "DemoPass123!"},
    {"username": "adj_priya",     "role": "ADJUSTER", "password": "DemoPass123!"},
    {"username": "test_adjuster", "role": "ADJUSTER", "password": "DemoPass123!"},
]

CLIENTS = [
    "Acme Corp",
    "Riverside Holdings",
    "Pinnacle Financial",
    "Global Tech Systems",
    "Apex Logistics",
]

POLICIES = [
    {"code": "cyber_sme",    "limit": 200000.00, "deductible": 5000.00},
    {"code": "auto_comp",    "limit": 30000.00,  "deductible": 500.00},
    {"code": "home_std",     "limit": 250000.00, "deductible": 1000.00},
    {"code": "health_p",     "limit": 25000.00,  "deductible": 250.00},
    {"code": "rent_std",     "limit": 25000.00,  "deductible": 250.00},
    {"code": "life_term",    "limit": 100000.00, "deductible": 0.00},
    {"code": "travel_basic", "limit": 15000.00,  "deductible": 100.00},
    {"code": "biz_liab",     "limit": 500000.00, "deductible": 2500.00},
    {"code": "marine_cargo", "limit": 75000.00,  "deductible": 1000.00},
    {"code": "pet_care",     "limit": 10000.00,  "deductible": 100.00},
]

CLAIMS = [
    {"client_idx": 0, "policy_code": "cyber_sme",    "adjuster": "demo_adjuster", "claim_date": date(2024, 1, 15), "status": "submitted"},
    {"client_idx": 1, "policy_code": "auto_comp",    "adjuster": "demo_adjuster", "claim_date": date(2024, 2, 10), "status": "decided", "final_payout": 4200.00},
    {"client_idx": 2, "policy_code": "home_std",     "adjuster": "adj_carlos",    "claim_date": date(2024, 3, 5),  "status": "pending"},
    {"client_idx": 3, "policy_code": "health_p",     "adjuster": "adj_carlos",    "claim_date": date(2024, 3, 20), "status": "decided", "final_payout": 1450.50},
    {"client_idx": 4, "policy_code": "rent_std",     "adjuster": "adj_priya",     "claim_date": date(2024, 4, 12), "status": "submitted"},
    {"client_idx": 0, "policy_code": "life_term",    "adjuster": "adj_priya",     "claim_date": date(2024, 4, 25), "status": "open"},
    {"client_idx": 1, "policy_code": "travel_basic", "adjuster": "demo_adjuster", "claim_date": date(2024, 5, 8),  "status": "decided", "final_payout": 750.00},
    {"client_idx": 2, "policy_code": "biz_liab",     "adjuster": "adj_carlos",    "claim_date": date(2024, 5, 30), "status": "submitted"},
    {"client_idx": 3, "policy_code": "marine_cargo", "adjuster": "adj_priya",     "claim_date": date(2024, 6, 14), "status": "decided", "final_payout": 18200.00},
    {"client_idx": 4, "policy_code": "pet_care",     "adjuster": "demo_adjuster", "claim_date": date(2024, 6, 28), "status": "pending"},
    {"client_idx": 0, "policy_code": "auto_comp",    "adjuster": "test_adjuster", "claim_date": date(2024, 7, 10), "status": "submitted"},
    {"client_idx": 1, "policy_code": "cyber_sme",    "adjuster": "test_adjuster", "claim_date": date(2024, 7, 22), "status": "decided", "final_payout": 12500.00},
    {"client_idx": 2, "policy_code": "health_p",     "adjuster": "demo_adjuster", "claim_date": date(2024, 8, 4),  "status": "submitted"},
    {"client_idx": 3, "policy_code": "biz_liab",     "adjuster": "adj_carlos",    "claim_date": date(2024, 8, 19), "status": "pending"},
    {"client_idx": 4, "policy_code": "travel_basic", "adjuster": "adj_priya",     "claim_date": date(2024, 9, 2),  "status": "decided", "final_payout": 1100.00},
]


class Command(BaseCommand):
    help = "Idempotent comprehensive dev seed: users, clients, policies, and claims variety."

    def handle(self, *args, **options):
        # ── Users ─────────────────────────────────────────────────────────
        created_users = {}
        for u in MANAGERS + ADJUSTERS:
            obj, created = User.objects.get_or_create(
                username=u["username"],
                defaults={"role": u["role"]},
            )
            if created:
                obj.set_password(u["password"])
                obj.save()
                self.stdout.write(f"  ✓ Created user: {u['username']}")
            else:
                self.stdout.write(f"  · Existing user: {u['username']}")
            created_users[u["username"]] = obj

        # ── Clients ───────────────────────────────────────────────────────
        client_objs = []
        for name in CLIENTS:
            obj, created = Client.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f"  ✓ Created client: {name}")
            client_objs.append(obj)

        default_client, _ = Client.objects.get_or_create(name="Default Synthetic Client")

        # ── Policy Versions by Code ───────────────────────────────────────
        policy_versions = {}
        for p_spec in POLICIES:
            code = p_spec["code"]
            policy, _ = Policy.objects.get_or_create(
                policy_number=code,
                defaults={"client": default_client},
            )
            pv = PolicyVersion.objects.filter(policy=policy).order_by("effective_from").first()
            if not pv:
                pv = PolicyVersion.objects.create(
                    policy=policy,
                    version="2024-01",
                    effective_from=date(2024, 1, 1),
                    policy_limit=p_spec["limit"],
                    deductible=p_spec["deductible"],
                )
            policy_versions[code] = pv
            self.stdout.write(f"  ✓ Policy version ready: {code} ({pv.version}, limit: ${pv.policy_limit})")

        # ── Seed Variety Claims ───────────────────────────────────────────
        for spec in CLAIMS:
            adjuster = created_users[spec["adjuster"]]
            client   = client_objs[spec["client_idx"]]
            claim_date = spec["claim_date"]
            pv = policy_versions[spec["policy_code"]]
            final_payout = spec.get("final_payout")

            obj, created = Claim.objects.get_or_create(
                client=client,
                adjuster=adjuster,
                claim_date=claim_date,
                defaults={
                    "policy_version": pv,
                    "status": spec["status"],
                    "final_payout": final_payout,
                },
            )
            if created:
                self.stdout.write(
                    f"  ✓ Claim {obj.id} — Client: {client.name} / Policy: {spec['policy_code']} / Adjuster: {adjuster.username} / Status: {spec['status']}"
                )
            else:
                updated_fields = []
                if obj.policy_version_id != pv.id:
                    obj.policy_version = pv
                    updated_fields.append("policy_version")
                if final_payout is not None and obj.final_payout != final_payout:
                    obj.final_payout = final_payout
                    updated_fields.append("final_payout")
                if updated_fields:
                    obj.save(update_fields=updated_fields)
                    self.stdout.write(f"  ✎ Updated claim {obj.id} → Policy: {spec['policy_code']}")
                else:
                    self.stdout.write(f"  · Existing claim: {obj.id} ({spec['policy_code']})")

        # ── Re-balance any pre-existing un-assigned/monolithic claims ───────
        all_pvs = list(policy_versions.values())
        unassigned_claims = Claim.objects.filter(policy_version__isnull=True)
        for i, claim in enumerate(unassigned_claims):
            pv = all_pvs[i % len(all_pvs)]
            claim.policy_version = pv
            claim.save(update_fields=["policy_version"])
            self.stdout.write(f"  ✎ Re-assigned legacy claim {claim.id} → Policy: {pv.policy.policy_number}")

        self.stdout.write(self.style.SUCCESS("\nSeed complete."))
        self.stdout.write(
            "\nDemo credentials (all passwords = DemoPass123!):\n"
            "  Manager:  demo_manager, mgr_sarah\n"
            "  Adjuster: demo_adjuster, adj_carlos, adj_priya, test_adjuster\n"
        )
