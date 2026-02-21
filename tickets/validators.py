import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_extension(value):
    """Validate that the uploaded file has an allowed extension."""
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_ATTACHMENT_EXTENSIONS:
        allowed = ', '.join(settings.ALLOWED_ATTACHMENT_EXTENSIONS)
        raise ValidationError(
            f'File type "{ext}" is not allowed. Allowed types: {allowed}'
        )


def validate_file_size(value):
    """Validate that the uploaded file does not exceed the maximum size."""
    if value.size > settings.MAX_ATTACHMENT_SIZE:
        max_size_mb = settings.MAX_ATTACHMENT_SIZE / (1024 * 1024)
        file_size_mb = value.size / (1024 * 1024)
        raise ValidationError(
            f'File size ({file_size_mb:.2f} MB) exceeds the maximum allowed size of {max_size_mb:.0f} MB.'
        )
