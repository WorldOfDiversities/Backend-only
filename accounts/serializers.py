from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserProfile
from django.utils import timezone
from datetime import timedelta
from .models import PasswordReset


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active"]
        read_only_fields = ["id", "is_active"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True,
    )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "user_id",
            "role",
            "phone_number",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]

    def validate_phone_number(self, value: str) -> str:
        cleaned = value.strip()
        if cleaned and len(cleaned) < 7:
            raise serializers.ValidationError("Phone number is too short.")
        return cleaned


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(
        choices=[UserProfile.Role.ADMIN, UserProfile.Role.MANAGER, UserProfile.Role.CASHIER],
        required=False,
        default=UserProfile.Role.CASHIER,
    )

    def validate_username(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Username is required.")
        if User.objects.filter(username__iexact=cleaned).exists():
            raise serializers.ValidationError("Username already exists.")
        return cleaned

    def validate_email(self, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned and User.objects.filter(email__iexact=cleaned).exists():
            raise serializers.ValidationError("Email already exists.")
        return cleaned

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        role = validated_data.pop("role", UserProfile.Role.CASHIER)
        password = validated_data.pop("password")

        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        user.set_password(password)
        user.save()

        profile = UserProfile.objects.create(user=user, role=role)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role,
        }


class RoleAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.ChoiceField(choices=[choice[0] for choice in UserProfile.Role.choices], write_only=True)

    def validate(self, attrs):
        selected_role = attrs.pop("role")
        data = super().validate(attrs)

        profile = getattr(self.user, "profile", None)
        if profile is None:
            raise serializers.ValidationError({"detail": "Account profile is missing."})

        if profile.role != selected_role:
            raise serializers.ValidationError({"detail": "Incorrect role selected."})

        data["role"] = profile.role
        data["username"] = self.user.username
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset (email lookup)"""
    email = serializers.EmailField()

    def validate_email(self, value):
        cleaned = value.strip().lower()
        if not User.objects.filter(email__iexact=cleaned).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return cleaned

    def create(self, validated_data):
        """Generate password reset token and return user"""
        email = validated_data['email']
        user = User.objects.get(email__iexact=email)
        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
		
        token = attrs.get('token')
        try:
            reset_obj = PasswordReset.objects.get(token=token)
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError({'token': 'Invalid reset token.'})
		
        if not reset_obj.is_valid():
            if reset_obj.is_used:
                raise serializers.ValidationError({'token': 'This reset link has already been used.'})
            else:
                raise serializers.ValidationError({'token': 'This reset link has expired.'})
		
        attrs['reset_obj'] = reset_obj
        return attrs

    def save(self):
        """Update password and mark token as used"""
        reset_obj = self.validated_data['reset_obj']
        user = reset_obj.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        reset_obj.mark_as_used()
        return user


class PasswordResetTokenValidateSerializer(serializers.Serializer):
    """Serializer for validating a password reset token"""
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            reset_obj = PasswordReset.objects.get(token=value)
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError('Invalid reset token.')
		
        if not reset_obj.is_valid():
            if reset_obj.is_used:
                raise serializers.ValidationError('This reset link has already been used.')
            else:
                raise serializers.ValidationError('This reset link has expired.')
		
        return value
