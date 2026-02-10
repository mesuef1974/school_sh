import pytest
from django.conf import settings
from coredata.models import Staff, JobTitle
from django.contrib.auth.models import User
import hashlib
import base64
from cryptography.fernet import Fernet

@pytest.mark.django_db
class TestSecurityEncryption:
    def test_encrypted_char_field_logic(self):
        """
        Verify that sensitive fields are encrypted in the database and decrypted on retrieval.
        """
        # 1. Create a JobTitle (dependency for Staff)
        job = JobTitle.objects.create(title="Test Job", code="TEST-001")
        
        # 2. Create a Staff member with sensitive data
        national_id = "12345678901"
        phone = "98765432"
        staff = Staff.objects.create(
            name="Test User",
            job_title=job,
            national_no=national_id,
            phone_no=phone
        )
        
        # 3. Retrieve from DB and verify decryption
        retrieved_staff = Staff.objects.get(id=staff.id)
        assert retrieved_staff.national_no == national_id
        assert retrieved_staff.phone_no == phone
        
        # 4. Verify Raw DB Value is actually encrypted
        # We can use a raw connection or check the dictionary values if possible
        # but the best way is to manually decrypt using the same logic
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        # Check that we can't find the plain text in the raw DB field
        # Note: In Django, getting a value usually invokes the field's from_db_value
        # To see the raw value, we can use .values() or .get_prep_value()
        field = Staff._meta.get_field('national_no')
        raw_val = field.get_prep_value(national_id)
        
        assert raw_val != national_id
        assert fernet.decrypt(raw_val.encode()).decode() == national_id

    def test_non_encrypted_fallback(self):
        """
        Verify that the field handles non-encrypted values gracefully (fallback).
        """
        # This is useful for migrated data that might not be encrypted yet
        # or if the encryption key changes
        job = JobTitle.objects.create(title="Fallback Job", code="FALLBACK-001")
        staff = Staff.objects.create(name="Fallback User", job_title=job)
        
        # Manually set a non-encrypted value (if we were to bypass Django's save)
        # For testing purposes, we can test the field's from_db_value directly
        field = Staff._meta.get_field('national_no')
        plain_value = "OLD_VALUE_123"
        
        # from_db_value(self, value, expression, connection)
        result = field.from_db_value(plain_value, None, None)
        assert result == plain_value
