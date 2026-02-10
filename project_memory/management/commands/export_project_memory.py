from django.core.management.base import BaseCommand
from project_memory.models import ProjectGoal, Technology, ArchitecturalDecision, GuidingPrinciple
import io
import os

class Command(BaseCommand):
    help = 'Exports the project memory context for AI model priming. Can write to stdout or a file.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Optional path to an output file. If provided, output is written here instead of stdout.',
        )

    def handle(self, *args, **options):
        """
        Gathers project memory data and formats it as a Markdown string.
        """
        output = io.StringIO()

        output.write("# ذاكرة مشروع منصة الشحانية الذكية\n\n")
        output.write("هذا ملخص تلقائي لذاكرة المشروع لتهيئة النموذج الذكي. استخدم هذا السياق لفهم المشروع بشكل أفضل.\n\n")

        # 1. أهداف المشروع
        try:
            goals = ProjectGoal.objects.all()
            if goals:
                output.write("## 1. أهداف المشروع الرئيسية\n")
                for goal in goals:
                    output.write(f"- **{goal.name} ({goal.get_goal_type_display()})**: {goal.description}\n")
                    if goal.kpi:
                        output.write(f"  - *مؤشر الأداء*: {goal.kpi}\n")
                output.write("\n")
        except Exception:
            output.write("## 1. أهداف المشروع الرئيسية (خطأ في الاستعلام)\n\n")


        # 2. المكدس التقني
        try:
            techs = Technology.objects.all()
            if techs:
                output.write("## 2. المكدس التقني (Tech Stack)\n")
                layers = {}
                for tech in techs:
                    if tech.layer not in layers:
                        layers[tech.layer] = []
                    layers[tech.layer].append(tech)
                
                for layer, tech_list in layers.items():
                    output.write(f"- **{layer}**:\n")
                    for tech in tech_list:
                        version = f" (v{tech.version})" if tech.version else ""
                        output.write(f"  - {tech.name}{version}: {tech.purpose}\n")
                output.write("\n")
        except Exception:
            output.write("## 2. المكدس التقني (Tech Stack) (خطأ في الاستعلام)\n\n")

        # 3. المبادئ التوجيهية
        try:
            principles = GuidingPrinciple.objects.all()
            if principles:
                output.write("## 3. المبادئ التوجيهية والحوكمة\n")
                for principle in principles:
                    output.write(f"- **{principle.name} ({principle.get_principle_type_display()})**: {principle.description}\n")
                output.write("\n")
        except Exception:
            output.write("## 3. المبادئ التوجيهية والحوكمة (خطأ في الاستعلام)\n\n")

        # 4. آخر القرارات المعمارية
        try:
            adrs = ArchitecturalDecision.objects.order_by('-date')[:5] # Get latest 5
            if adrs:
                output.write("## 4. آخر القرارات المعمارية (Latest ADRs)\n")
                for adr in adrs:
                    output.write(f"- **{adr.adr_id} ({adr.date})**: {adr.title} - **الحالة: {adr.status}**\n")
                output.write("\n")
        except Exception:
            output.write("## 4. آخر القرارات المعمارية (Latest ADRs) (خطأ في الاستعلام)\n\n")

        # Get the final content
        content = output.getvalue()

        output_file = options['file']
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.stdout.write(self.style.SUCCESS(f"Successfully exported project memory to {output_file}"))
            except IOError as e:
                self.stderr.write(self.style.ERROR(f"Error writing to file {output_file}: {e}"))
        else:
            # Ensure stdout is configured for UTF-8 if possible
            import sys
            sys.stdout.reconfigure(encoding='utf-8')
            self.stdout.write(content)