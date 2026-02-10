from rest_framework import viewsets
from .models import ArchitecturalDecision, ProjectGoal, Technology, GuidingPrinciple
from .serializers import (
    ArchitecturalDecisionSerializer, 
    ProjectGoalSerializer, 
    TechnologySerializer, 
    GuidingPrincipleSerializer
)

class TechnologyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows the tech stack to be viewed.
    """
    queryset = Technology.objects.all()
    serializer_class = TechnologySerializer

class LatestADRsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that returns the 5 most recent ADRs.
    """
    queryset = ArchitecturalDecision.objects.order_by('-date', '-adr_id')[:5]
    serializer_class = ArchitecturalDecisionSerializer

class ProjectGoalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows project goals to be viewed.
    """
    queryset = ProjectGoal.objects.all()
    serializer_class = ProjectGoalSerializer