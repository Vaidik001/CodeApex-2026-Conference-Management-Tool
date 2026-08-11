from django.core.validators import RegexValidator

indian_mobile_validator = RegexValidator(
    regex=r'^[6-9]\d{9}$',
    message='Enter a valid 10-digit Indian mobile number (e.g. 9876543210).',
)
