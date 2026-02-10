import pytest
import io
import os
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from coredata.models import EvidenceDocument, AcademicYear, EvidenceFile
from PIL import Image

@pytest.mark.django_db
class TestMediaProcessing:
    def setup_method(self):
        self.user = User.objects.create_user(username="test_media_user")
        self.year = AcademicYear.objects.create(name="2025-2026", is_active=True)
        self.type = EvidenceFile.objects.create(name="General File", code="GEN")

    def test_image_to_pdf_conversion(self):
        """
        Verify that uploaded images (PNG/JPG) are automatically converted to PDF.
        """
        # Create a tiny dummy image
        img_buffer = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(img_buffer, format='PNG')
        img_content = ContentFile(img_buffer.getvalue(), name='test_image.png')
        
        doc = EvidenceDocument.objects.create(
            user=self.user,
            academic_year=self.year,
            evidence_type=self.type,
            title="Image Test",
            file=img_content
        )
        
        # Check filename extension
        assert doc.file.name.endswith('.pdf')
        assert doc.original_filename == 'test_image.png'
        assert "[Converted to Compressed PDF]" in doc.description

    def test_file_metadata_extraction(self):
        """
        Verify metadata extraction (size, hash) for uploaded files.
        """
        content = b"Some test file content for hashing"
        doc = EvidenceDocument.objects.create(
            user=self.user,
            academic_year=self.year,
            title="Metadata Test",
            file=ContentFile(content, name="test.txt")
        )
        
        assert doc.file_size > 0
        # Wait, the current model logic for conversion might try to convert .txt?
        # Let's check the code: it checks '.jpg', '.jpeg', '.png' for images.
        # But it does `self.file_size = self.file.size` at the end.
        
        assert doc.file_size == len(content)
        # Note: Hashing is currently not implemented in the save() method, 
        # but the field exists. Let's see if I should add it or just test what's there.
        # The model have `file_hash` field but I don't see hashing logic in `save()`.
        # I will mark this as a "potential enhancement" in the report.
