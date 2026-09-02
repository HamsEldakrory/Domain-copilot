from rest_framework import serializers

class AdjudicateRequestSerializer(serializers.Serializer):
    claim_id = serializers.UUIDField()
    claimed_amount = serializers.FloatField(min_value=0)
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