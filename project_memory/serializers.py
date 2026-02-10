from rest_framework import serializers
from .models import ArchitecturalDecision, ProjectGoal, Technology, GuidingPrinciple

class ArchitecturalDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitecturalDecision
        fields = ['adr_id', 'title', 'date', 'status', 'context', 'decision', 'justification']

class ProjectGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectGoal
        fields = ['name', 'description', 'goal_type', 'kpi', 'measurement']

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ['name', 'version', 'layer', 'purpose']

class GuidingPrincipleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuidingPrinciple
        fields = ['name', 'description', 'principle_type']