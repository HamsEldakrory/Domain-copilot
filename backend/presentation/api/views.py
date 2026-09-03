import os
from statistics import correlation
from celery import uuid
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser
from rest_framework.parsers import FormParser
from rest_framework.views import APIView, settings
from rest_framework.response import Response
from rest_framework import status
from config.settings import CELERY_BROKER_URL
from presentation.api.permissions import CanAccessClaim, IsManager
from infrastructure.tasks import adjudicate_claim_task,ingest_document_task
from infrastructure.persistence.models import Document, Job, User, Policy, PolicyVersion, Document, Client as ClientModel
from application.use_cases.cancel_job import CancelJobUseCase
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.db import IntegrityError
from presentation.api.serializers import (
    AdjudicateRequestSerializer, JobSubmittedResponseSerializer,CreateAdjusterRequestSerializer,
    JobStatusResponseSerializer, CancelResponseSerializer, ErrorResponseSerializer,DocumentStatusSerializer, UserBasicSerializer,
    PolicyUploadSerializer
)
class AdjudicateView(APIView):
    permission_classes = [IsAuthenticated, CanAccessClaim]
    @extend_schema(
        request=AdjudicateRequestSerializer,
        responses={202: JobSubmittedResponseSerializer, 403: ErrorResponseSerializer},
        description="Submit a claim for async adjudication. Returns job_id immediately (T7).",
    )
    def post(self, request):
        serializer = AdjudicateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        claim_id = str(serializer.validated_data["claim_id"])
        claimed_amount = serializer.validated_data["claimed_amount"]
        deductible_override = serializer.validated_data.get("deductible_override")
        correlation_id=getattr(request, "correlation_id", str(uuid.uuid4()))
        job = Job.objects.create(claim_id=claim_id, status="QUEUED")
        adjudicate_claim_task.delay(str(job.id), claim_id, claimed_amount, correlation_id, deductible_override)
        return Response({"job_id": str(job.id), "status": "QUEUED", "correlation_id": correlation_id}, status=status.HTTP_202_ACCEPTED)
class CreateAdjusterView(APIView):
    permission_classes = [IsAuthenticated, IsManager]
    @extend_schema(
        request=CreateAdjusterRequestSerializer,
        responses={201: UserBasicSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
        description="Manager-only: create a new Adjuster account. Role is always ADJUSTER, regardless of any role value sent - this endpoint cannot be used to create another Manager.",
    )
    def post(self, request):
        serializer = CreateAdjusterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if User.objects.filter(username=serializer.validated_data["username"]).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User(
            username=serializer.validated_data["username"],
            email=serializer.validated_data.get("email", ""),
            role="ADJUSTER",  # hardcoded, deliberately ignores any "role" the caller might send
        )
        user.set_password(serializer.validated_data["password"])
        user.save()

        return Response(UserBasicSerializer(user).data, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserBasicSerializer},
        description="Return the authenticated user's own info. Uses request.user only - no id parameter accepted.",
    )
    def get(self, request):
        return Response(UserBasicSerializer(request.user).data)

class JobStatusView(APIView):
    permission_classes = [IsAuthenticated, CanAccessClaim]
    @extend_schema(
        responses={200: JobStatusResponseSerializer, 404: ErrorResponseSerializer},
        description="Check the current status of an adjudication job.",
    )
    def get(self, request, job_id):
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"job_id": str(job.id), "status": job.status})
    
from application.use_cases.cancel_job import CancelJobUseCase
from infrastructure.persistence.django_agent_run_recorder import DjangoAgentRunRecorder
from infrastructure.persistence.django_approval_repository import DjangoApprovalRepository
from infrastructure.events.redis_job_event_publisher import RedisJobEventPublisher


class CancelJobView(APIView):
    permission_classes = [IsAuthenticated, CanAccessClaim]
    @extend_schema(
        request=None,
        responses={200: CancelResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer},
        description="Cancel a running or queued job. Cooperative cancellation - stops between pipeline steps and mid-token-stream.",
    )
    def post(self, request, job_id):
        event_publisher = RedisJobEventPublisher()
        use_case = CancelJobUseCase(
            DjangoAgentRunRecorder(event_publisher=event_publisher),
            DjangoApprovalRepository(),
        )
        result = use_case.execute(str(job_id))
        if not result.success:
            code = status.HTTP_404_NOT_FOUND if result.error == "Job not found" else status.HTTP_400_BAD_REQUEST
            return Response({"error": result.error}, status=code)
        return Response({"job_id": str(job_id), "status": "CANCELLED"})

class PolicyUploadView(APIView):
    permission_classes = [IsAuthenticated, IsManager]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=PolicyUploadSerializer,
        responses={202: DocumentStatusSerializer, 403: ErrorResponseSerializer, 400: ErrorResponseSerializer},
        description="Manager-only: upload a new policy document. Limit/deductible set directly here, closing the manual-sync gap from ADR-008. Ingestion runs async.",
    )
    def post(self, request):
        serializer = PolicyUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        org, _ = ClientModel.objects.get_or_create(name="Default Synthetic Client")
        policy, _ = Policy.objects.get_or_create(client=org, policy_number=v["policy_number"])
        policy_version, _ = PolicyVersion.objects.update_or_create(
            policy=policy, version=v["version"],
            defaults={
                "effective_from": v["effective_from"], "effective_to": v.get("effective_to"),
                "policy_limit": v["policy_limit"], "deductible": v["deductible"],
            },
        )

        uploaded = v["file"]
        ext = uploaded.name.lower().rsplit(".", 1)[-1]
        saved_path = default_storage.save(f"policy_uploads/{uploaded.name}", uploaded)
        abs_path = default_storage.path(saved_path)

        document = Document.objects.create(
            policy_version=policy_version, filename=uploaded.name, file_type=ext, status="pending",
        )
        ingest_document_task.delay(str(document.id), abs_path, ext)

        return Response(DocumentStatusSerializer(document).data, status=status.HTTP_202_ACCEPTED)


class DocumentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: DocumentStatusSerializer, 404: ErrorResponseSerializer})
    def get(self, request, document_id):
        doc = Document.objects.filter(id=document_id).first()
        if not doc:
            return Response({"error": "Not found"}, status=404)
        return Response(DocumentStatusSerializer(doc).data)
class HealthView(APIView):
    permission_classes = []
    def get(self, request):
        return Response({"status": "ok"})

class ReadinessView(APIView):
    permission_classes = []
    def get(self, request):
        from django.db import connection
        import redis
        checks = {}
        try:
            connection.cursor()
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e}"
        try:
            redis.Redis.from_url(settings.CELERY_BROKER_URL).ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
        ready = all(v == "ok" for v in checks.values())
        return Response(checks, status=200 if ready else 503)