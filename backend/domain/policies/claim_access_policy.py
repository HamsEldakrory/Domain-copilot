def can_access_claim(user_role: str, user_id: str, claim_adjuster_id: str) -> bool:
    """
    Adjuster: can only access claims assigned to them.
    Manager: can access any claim within the system (BRD 2.2 - Manager
    has broader visibility over claims within their management scope;
    scope is simplified to "all claims" for this MVP, not sub-teams).
    """
    if user_role == "MANAGER":
        return True
    return str(user_id) == str(claim_adjuster_id)