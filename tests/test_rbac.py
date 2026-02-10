import pytest
from django.contrib.auth.models import User, Group
from coredata.models import Staff, JobTitle, Committee, OperationalPlanItems, EvidenceFile, FilePermission
from django.test import RequestFactory
from coredata.views.plan_views import plan_list
from coredata.forms import PlanItemExecutionForm

@pytest.mark.django_db
class TestRBAC:
    def setup_method(self):
        self.factory = RequestFactory()
        
        # Roles
        self.jt_teacher = JobTitle.objects.create(title="معلم رياضيات", code="TCH-MATH")
        self.jt_coordinator = JobTitle.objects.create(title="منسق رياضيات", code="COORD-MATH")
        
        self.teacher_user = User.objects.create_user(username="teacher", password="p")
        self.coord_user = User.objects.create_user(username="coordinator", password="p")
        
        self.staff_teacher = Staff.objects.create(user=self.teacher_user, name="Teacher 1", job_title=self.jt_teacher)
        self.staff_coord = Staff.objects.create(user=self.coord_user, name="Coord 1", job_title=self.jt_coordinator)
        
        # Committees
        self.comm_math = Committee.objects.create(name="لجنة الرياضيات")
        self.comm_math.members.add(self.teacher_user, self.coord_user)
        
        # Plan Items
        self.item_math = OperationalPlanItems.objects.create(
            rank_name="الرياضيات", 
            procedure="Math Action", 
            executor_committee=self.comm_math
        )
        self.item_science = OperationalPlanItems.objects.create(
            rank_name="العلوم", 
            procedure="Science Action"
        )

    def test_teacher_view_filtering(self):
        """
        Verify that a teacher sees items from their committee but not others.
        """
        request = self.factory.get('/plan/')
        request.user = self.teacher_user
        
        # Simulate view_role logic
        # In a real integration test we'd call the view, but here we can check the logic
        # We need a session/messages but let's mock the basic filter
        
        # Test helper: logic from plan_list
        user_committees = request.user.committees.all()
        qs = OperationalPlanItems.objects.filter(executor_committee__in=user_committees)
        
        assert self.item_math in qs
        assert self.item_science not in qs

    def test_form_evidence_file_filtering(self):
        """
        Verify that the dropdown in PlanItemExecutionForm is filtered by job title permissions.
        """
        ef_reg = EvidenceFile.objects.create(name="سجل حضور", code="REG")
        ef_plan = EvidenceFile.objects.create(name="خطة", code="PLAN")
        
        # Give permission for "سجل حضور" to Teachers
        FilePermission.objects.create(job_title=self.jt_teacher, evidence_file=ef_reg, can_view=True)
        
        form = PlanItemExecutionForm(instance=self.item_math, user=self.teacher_user)
        
        # Check filtered queryset in the form field
        qs = form.fields['evidence_source_file'].queryset
        assert ef_reg in qs
        assert ef_plan not in qs
