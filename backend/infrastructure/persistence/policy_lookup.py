from infrastructure.persistence.models import PolicyVersion


def django_policy_limit_lookup(policy_version_id: str) -> tuple[float, float]:
    pv = PolicyVersion.objects.filter(id=policy_version_id).first()
    if not pv:
        return 0.0, 0.0
    return float(pv.policy_limit or 0), float(pv.deductible or 0)