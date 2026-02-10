import pytest
from coredata.models import OperationalPlanItems, AcademicYear
from django.utils import timezone

@pytest.mark.django_db
class TestDataIntegrity:
    def setup_method(self):
        self.year = AcademicYear.objects.create(name="2025-2026", is_active=True)

    def test_digital_seal_generation(self):
        """
        Verify that a digital seal is generated when a plan item is completed.
        """
        item = OperationalPlanItems.objects.create(
            academic_year=self.year,
            rank_name="Test Area",
            procedure="Test Procedure",
            status="In Progress"
        )
        
        assert item.digital_seal is None
        
        # Set to Completed
        item.status = "Completed"
        item.save()
        
        assert item.digital_seal is not None
        assert len(item.digital_seal) == 64 # SHA-256 length

    def test_digital_seal_integrity(self):
        """
        Verify that modifying key fields changes the generated seal.
        """
        item = OperationalPlanItems.objects.create(
            academic_year=self.year,
            rank_name="Integrity Area",
            procedure="Original Procedure",
            status="Completed"
        )
        
        original_seal = item.digital_seal
        assert original_seal is not None
        
        # If we clear it and save again with same data, it should match
        item.digital_seal = None
        item.save()
        assert item.digital_seal == original_seal
        
        # If we change data and regenerate, it should differ
        item.procedure = "Modified Procedure"
        # Since the auto-generation only happens if status=='Completed' and not digital_seal,
        # we clear it to force regeneration for the test
        item.digital_seal = None
        item.save()
        
        assert item.digital_seal != original_seal
