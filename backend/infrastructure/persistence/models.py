import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from pgvector.django import VectorField


class User(AbstractUser):
    ROLE_CHOICES = [
        ("ADJUSTER", "Adjuster"),
        ("MANAGER", "Manager"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="ADJUSTER")


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Policy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="policies")
    policy_number = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class PolicyVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="versions")
    version = models.CharField(max_length=50)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    policy_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deductible = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_version = models.ForeignKey(PolicyVersion, on_delete=models.CASCADE, related_name="documents")
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default="pending")
    content_hash = models.CharField(max_length=64, blank=True)
    error_message = models.TextField(blank=True)
    embedding_provider = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    page_number = models.IntegerField(null=True, blank=True)
    section = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    clause = models.CharField(max_length=50, blank=True)
    search_content = models.TextField(blank=True)
    embedding = VectorField(dimensions=None, null=True, blank=True)


class Claim(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="claims")
    policy_version = models.ForeignKey(
        PolicyVersion, on_delete=models.PROTECT, null=True, blank=True, related_name="claims"
    )
    adjuster = models.ForeignKey(User, on_delete=models.PROTECT, related_name="claims")
    claim_date = models.DateField()
    status = models.CharField(max_length=50, default="submitted")
    created_at = models.DateTimeField(auto_now_add=True)


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=30, default="QUEUED")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JobStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="steps")
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="PENDING")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class AgentRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="agent_runs")
    agent_name = models.CharField(max_length=100)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Approval(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name="approvals")
    status = models.CharField(max_length=20, blank=True)  # approve / reject / edit
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Decision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="decisions")
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="decisions")
    outcome = models.CharField(max_length=50)
    rationale = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    agent_run = models.ForeignKey(AgentRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)