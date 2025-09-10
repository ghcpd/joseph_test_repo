from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "age", "gender"]

    def validate_age(self, value):
        if value < 10 or value > 120:
            raise serializers.ValidationError("Age must be between 10 and 120")
        return value
