from rest_framework import serializers
from infrastructure.persistence.models import Claim, Client, Document, PolicyVersion, User


class AdjudicateRequestSerializer(serializers.Serializer):
    claim_id = serializers.UUIDField()
    claimed_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, coerce_to_string=False)
    deductible_override = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        required=False, allow_null=True, coerce_to_string=False,
    )


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
    policy_limit = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, coerce_to_string=False,
    )
    deductible = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, coerce_to_string=False,
    )

    def validate_file(self, value):
        ext = value.name.lower().rsplit(".", 1)[-1]
        if ext not in ("pdf", "docx"):
            raise serializers.ValidationError("Only .pdf and .docx files are accepted")
        return value


class DocumentStatusSerializer(serializers.ModelSerializer):
    policy_number = serializers.CharField(
        source="policy_version.policy.policy_number", read_only=True, default=None,
    )
    policy_version = serializers.CharField(
        source="policy_version.version", read_only=True, default=None,
    )
    policy_limit = serializers.DecimalField(
        source="policy_version.policy_limit", max_digits=12, decimal_places=2,
        read_only=True, default=None, coerce_to_string=True,
    )
    deductible = serializers.DecimalField(
        source="policy_version.deductible", max_digits=12, decimal_places=2,
        read_only=True, default=None, coerce_to_string=True,
    )
    chunk_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Document
        fields = [
            "id",
            "filename",
            "status",
            "policy_number",
            "policy_version",
            "policy_limit",
            "deductible",
            "chunk_count",
            "error_message",
            "created_at",
        ]


class ClaimListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)
    policy_number = serializers.CharField(
        source="policy_version.policy.policy_number", read_only=True, default=None,
    )
    policy_version = serializers.CharField(
        source="policy_version.version", read_only=True, default=None,
    )
    policy_version_id = serializers.UUIDField(source="policy_version.id", read_only=True, default=None)
    policy_limit = serializers.DecimalField(
        source="policy_version.policy_limit", max_digits=12, decimal_places=2,
        read_only=True, default=None, coerce_to_string=True,
    )
    deductible = serializers.DecimalField(
        source="policy_version.deductible", max_digits=12, decimal_places=2,
        read_only=True, default=None, coerce_to_string=True,
    )
    adjuster_name = serializers.CharField(source="adjuster.username", read_only=True, default=None)
    adjuster_email = serializers.CharField(source="adjuster.email", read_only=True, default=None)
    final_payout = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True, coerce_to_string=True,
    )

    class Meta:
        model = Claim
        fields = [
            "id",
            "client_name",
            "policy_number",
            "policy_version",
            "policy_version_id",
            "policy_limit",
            "deductible",
            "adjuster_name",
            "adjuster_email",
            "claim_date",
            "status",
            "final_payout",
            "created_at",
        ]


class AskRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    policy_version_id = serializers.UUIDField(required=False)


class ApprovalDecisionRequestSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject", "edit"])
    outcome = serializers.CharField(required=False, allow_blank=True)
    rationale = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    final_payout = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, coerce_to_string=False,
    )
    original_recommendation = serializers.DictField(required=False, allow_null=True)


class CreateClaimSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    policy_version_id = serializers.UUIDField(required=False, allow_null=True)
    claim_date = serializers.DateField()


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name"]


class PolicyVersionOptionSerializer(serializers.ModelSerializer):
    policy_number = serializers.CharField(source="policy.policy_number", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = PolicyVersion
        fields = ["id", "policy_number", "version", "label", "effective_from", "effective_to"]

    def get_label(self, obj):
        return f"{obj.policy.policy_number} — v{obj.version}"