from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'age', 'gender', 'created_at']
        
    def validate_name(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Name cannot be empty.")
        return value.strip()
    
    def validate_age(self, value):
        if value < 10 or value > 120:
            raise serializers.ValidationError("Age must be between 10 and 120.")
        return value
    
    def validate_email(self, value):
        # Check for existing email, but exclude current instance during updates
        existing_user = User.objects.filter(email=value)
        if self.instance:
            existing_user = existing_user.exclude(pk=self.instance.pk)
        if existing_user.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value