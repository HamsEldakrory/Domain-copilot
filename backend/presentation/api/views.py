from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from presentation.api.permissions import CanAccessClaim
from presentation.api.serializers import AdjudicateRequestSerializer
from infrastructure.tasks import adjudicate_claim_task
from infrastructure.persistence.models import Job
from application.use_cases.cancel_job import CancelJobUseCase
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from presentation.api.serializers import (
    AdjudicateRequestSerializer, JobSubmittedResponseSerializer,
    JobStatusResponseSerializer, CancelResponseSerializer, ErrorResponseSerializer,
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
        job = Job.objects.create(claim_id=claim_id, status="QUEUED")
        adjudicate_claim_task.delay(str(job.id), claim_id, claimed_amount)
        return Response({"job_id": str(job.id), "status": "QUEUED"}, status=status.HTTP_202_ACCEPTED)

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