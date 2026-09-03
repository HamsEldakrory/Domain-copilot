from rest_framework import serializers
from infrastructure.persistence.models import Claim, Document, User

class AdjudicateRequestSerializer(serializers.Serializer):
    claim_id = serializers.UUIDField()
    claimed_amount = serializers.FloatField(min_value=0)
    deductible_override = serializers.FloatField(min_value=0, required=False, allow_null=True)

class CreateAdjusterRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
class JobSubmittedResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()


class JobStatusResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()


class CancelResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
class PolicyUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    policy_number = serializers.CharField()
    version = serializers.CharField()
    effective_from = serializers.DateField()
    effective_to = serializers.DateField(required=False, allow_null=True)
    policy_limit = serializers.DecimalField(max_digits=12, decimal_places=2)
    deductible = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_file(self, value):
        ext = value.name.lower().rsplit(".", 1)[-1]
        if ext not in ("pdf", "docx"):
            raise serializers.ValidationError("Only .pdf and .docx files are accepted")
        return value


class DocumentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "filename", "status", "error_message"]

class ClaimListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ["id", "claim_date", "status", "created_at"]

class AskRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    policy_version_id = serializers.UUIDField(required=False)

class ApprovalDecisionRequestSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject", "edit"])
    outcome = serializers.CharField(required=False, allow_blank=True)
    rationale = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)