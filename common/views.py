import os
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole

from .models import SystemSettings
from .serializers import SystemSettingsSerializer


class SystemSettingsView(APIView):
	permission_classes = [IsAuthenticated, IsAdminRole]

	@staticmethod
	def _extract_media_path(raw_url: str | None) -> str:
		if not raw_url:
			return ""

		parsed = urlparse(str(raw_url))
		candidate = parsed.path or str(raw_url)
		media_url = str(settings.MEDIA_URL or "/media/")

		if not media_url.startswith("/"):
			media_url = f"/{media_url}"
		if not media_url.endswith("/"):
			media_url = f"{media_url}/"

		if not candidate.startswith(media_url):
			return ""

		relative_path = candidate[len(media_url):].lstrip("/")
		if not relative_path.startswith("settings/"):
			return ""

		return relative_path

	@classmethod
	def _delete_media_if_replaced(cls, old_url: str | None, new_url: str | None):
		old_path = cls._extract_media_path(old_url)
		new_path = cls._extract_media_path(new_url)

		if not old_path:
			return
		if old_path == new_path:
			return

		if default_storage.exists(old_path):
			default_storage.delete(old_path)

	@staticmethod
	def _get_singleton() -> SystemSettings:
		settings, _ = SystemSettings.objects.get_or_create(key="default")
		return settings

	def get(self, request):
		settings = self._get_singleton()
		serializer = SystemSettingsSerializer(settings)
		return Response(serializer.data)

	def put(self, request):
		settings = self._get_singleton()
		old_logo = str((settings.store_profile or {}).get("logo_data_url") or "")
		old_profile_photo = str((settings.appearance or {}).get("profile_photo_data_url") or "")

		serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		saved = serializer.save()

		new_logo = str((saved.store_profile or {}).get("logo_data_url") or "")
		new_profile_photo = str((saved.appearance or {}).get("profile_photo_data_url") or "")

		self._delete_media_if_replaced(old_logo, new_logo)
		self._delete_media_if_replaced(old_profile_photo, new_profile_photo)

		return Response(SystemSettingsSerializer(saved).data)


class SystemSettingsImageUploadView(APIView):
	permission_classes = [IsAuthenticated, IsAdminRole]
	parser_classes = [MultiPartParser, FormParser]

	ALLOWED_TARGETS = {"store_logo", "profile_photo"}
	ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
	MAX_SIZE_BYTES = 2 * 1024 * 1024

	def post(self, request):
		image_file = request.FILES.get("image")
		target = str(request.data.get("target", "")).strip().lower()

		if target not in self.ALLOWED_TARGETS:
			return Response({"detail": "Invalid target."}, status=status.HTTP_400_BAD_REQUEST)

		if not image_file:
			return Response({"detail": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

		ext = os.path.splitext(image_file.name)[1].lower()
		if ext not in self.ALLOWED_EXTENSIONS:
			return Response({"detail": "Unsupported file type."}, status=status.HTTP_400_BAD_REQUEST)

		if image_file.size > self.MAX_SIZE_BYTES:
			return Response({"detail": "File exceeds 2MB limit."}, status=status.HTTP_400_BAD_REQUEST)

		user_id = getattr(request.user, "id", "anon")
		file_name = f"{target}-{user_id}-{uuid.uuid4().hex}{ext}"
		relative_path = os.path.join("settings", target, file_name).replace("\\", "/")
		saved_path = default_storage.save(relative_path, ContentFile(image_file.read()))
		file_url = default_storage.url(saved_path)
		absolute_url = request.build_absolute_uri(file_url)

		return Response({
			"target": target,
			"url": absolute_url,
			"path": file_url,
		})
