from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from presentation.api.permissions import CanAccessClaim, IsManager
from presentation.api.serializers import AdjudicateRequestSerializer, CreateAdjusterRequestSerializer, UserBasicSerializer, ErrorResponseSerializer
from infrastructure.tasks import adjudicate_claim_task
from infrastructure.persistence.models import Job, User
from application.use_cases.cancel_job import CancelJobUseCase
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.db import IntegrityError

class AdjudicateView(APIView):
    permission_classes = [IsAuthenticated, CanAccessClaim]
    def post(self, request):
        serializer = AdjudicateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        claim_id = str(serializer.validated_data["claim_id"])
        claimed_amount = serializer.validated_data["claimed_amount"]
        job = Job.objects.create(claim_id=claim_id, status="QUEUED")
        adjudicate_claim_task.delay(str(job.id), claim_id, claimed_amount)
        return Response({"job_id": str(job.id), "status": "QUEUED"}, status=status.HTTP_202_ACCEPTED)
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