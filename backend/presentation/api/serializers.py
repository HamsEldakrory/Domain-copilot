from rest_framework import serializers
from infrastructure.persistence.models import User

class AdjudicateRequestSerializer(serializers.Serializer):
    claim_id = serializers.UUIDField()
    claimed_amount = serializers.FloatField(min_value=0)


class CreateAdjusterRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]