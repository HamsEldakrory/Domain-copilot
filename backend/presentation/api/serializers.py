from rest_framework import serializers

class AdjudicateRequestSerializer(serializers.Serializer):
    claim_id = serializers.UUIDField()
    claimed_amount = serializers.FloatField(min_value=0)