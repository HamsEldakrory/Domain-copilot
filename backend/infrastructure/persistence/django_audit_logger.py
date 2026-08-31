from domain.ports.audit_logger import AuditLogger
from infrastructure.persistence.models import AuditLog

class DjangoAuditLogger(AuditLogger):
    def log(self, job_id, actor_id, action, metadata):
        AuditLog.objects.create(job_id=job_id, actor_id=actor_id, action=action, metadata=metadata)