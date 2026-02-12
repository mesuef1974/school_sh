from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
import json
from django.contrib.auth.models import Group

from ..models import OperationalPlanItems, Committee, Staff
from ..forms.plan_forms import PlanItemExecutionForm, PlanItemEvaluationForm, EvidenceUploadForm

# The data loading block has been completely removed.

def get_chart_data(queryset, field):
    """Helper function to prepare data for Chart.js."""
    color_maps = {
        'follow_up': {"تم الإنجاز": "#10b981", "مكتمل": "#10b981", "لم يتم الإنجاز": "#ef4444", "مؤجل": "#f59e0b", "قيد الإنجاز": "#3b82f6", "جزئي": "#f59e0b"},
        'evaluation': {"مطابق": "#10b981", "مطابق جزئي": "#f59e0b", "غير مطابق": "#ef4444", "مرتفع": "#10b981", "متوسط": "#f59e0b", "منخفض": "#ef4444"}
    }
    color_map = color_maps.get(field, {})
    default_color = "#e5e7eb"
    stats_raw = queryset.values(field).annotate(count=Count('id')).order_by('-count')
    labels = [item.get(field) or 'غير مصنف' for item in stats_raw]
    data = [item['count'] for item in stats_raw]
    colors = [color_map.get(label, default_color) for label in labels]
    return {'labels': labels, 'datasets': [{'data': data, 'backgroundColor': colors, 'borderWidth': 2, 'borderColor': '#ffffff', 'hoverOffset': 4}]}

@login_required
def plan_list(request):
    """
    Displays the operational plan items. This view is now clean and stable.
    """
    qs = OperationalPlanItems.objects.all()
    user_committees = request.user.committees.all()

    # --- Role-Based View Filtering ---
    view_role = request.GET.get('view_role')
    
    # 1. Determine if the user has any items as executor or evaluator across the WHOLE plan
    is_executor_role = OperationalPlanItems.objects.filter(executor_committee__in=user_committees).exists()
    is_evaluator_role = OperationalPlanItems.objects.filter(evaluator_committee__in=user_committees).exists()

    # Default logic for initial load:
    # If no view_role is provided, set it based on priority
    if not view_role:
        if is_executor_role:
            view_role = 'executor'
        elif is_evaluator_role:
            view_role = 'evaluator'
        else:
            view_role = 'executor' # Default fallback

    if not request.user.is_superuser:
        if view_role == 'executor':
            # مهامي كمنفذ: البنود التي أنا عضو في لجنتها المنفذة
            qs = qs.filter(executor_committee__in=user_committees)
        elif view_role == 'evaluator':
            # مهامي كمقيم: البنود التي أنا مكلف بتقييمها رسمياً (المحاور الستة)
            qs = qs.filter(evaluator_committee__in=user_committees)
        else:
            # افتراضياً (للعرض فقط): يرى الموظف (المعلم) بنود قسمه التنفيذية
            # 1. Start with committees user belongs to directly
            query = Q(executor_committee__in=user_committees) | Q(evaluator_committee__in=user_committees)
            
            # 2. Add Dept/Section logic based on JOB TITLE (Critical for Teachers)
            try:
                # IMPORTANT: We use the Staff record because some users might not be in Committees yet
                staff_profile = Staff.objects.filter(user=request.user).first()
                if staff_profile and staff_profile.job_title:
                    job_title_text = staff_profile.job_title.title.strip()
                    
                    # Subjects mapping for broader coverage
                    subjects_map = {
                        "الرياضيات": ["رياضيات", "الرياضيات"],
                        "العربية": ["العربية", "اللغة العربية"],
                        "الانجليزية": ["الإنجليزية", "اللغة الانجليزية", "اللغة الإنجليزية"],
                        "الاسلامية": ["الاسلامية", "الإسلامية", "التربية الإسلامية", "العلوم الشرعية"],
                        "العلوم": ["العلوم", "الكيمياء", "الفيزياء", "الأحياء"],
                        "الاجتماعية": ["الاجتماعية", "العلوم الاجتماعية", "الدراسات الاجتماعية"],
                        "تكنولوجيا": ["تكنولوجيا", "الحاسوب"],
                        "البدنية": ["البدنية", "الرياضة"],
                        "النفسي": ["النفسي", "الأخصائي النفسي"],
                        "الاجتماعي": ["الاجتماعي", "الأخصائي الاجتماعي"],
                    }
                    
                    target_subject = None
                    for key, keywords in subjects_map.items():
                        if any(kw in job_title_text for kw in keywords):
                            target_subject = key
                            # If we found a match, search for committees with similar keywords
                            # and importantly include 'منسق'
                            keywords + ["منسق"]
                            coord_comms = Committee.objects.filter(
                                Q(name__icontains="منسق") & 
                                Q(name__icontains=target_subject)
                            )
                            if coord_comms.exists():
                                query |= Q(executor_committee__in=coord_comms)
                            break
            except Exception:
                pass
            
            qs = qs.filter(query).distinct()

    # --- Filtering Logic ---
    year = request.GET.get('year')
    if year: qs = qs.filter(year=year)

    rank_name = request.GET.get('rank_name')
    if rank_name: qs = qs.filter(rank_name=rank_name)

    executor = request.GET.get('executor')
    if executor: qs = qs.filter(executor=executor)

    date_range = request.GET.get('date_range')
    if date_range: qs = qs.filter(date_range=date_range)

    follow_up = request.GET.get('follow_up')
    if follow_up: qs = qs.filter(follow_up=follow_up)

    evaluation = request.GET.get('evaluation')
    if evaluation: qs = qs.filter(evaluation=evaluation)

    status_filter = request.GET.get('status')
    if status_filter: qs = qs.filter(status=status_filter)

    evidence_requested_filter = request.GET.get('evidence_requested')
    if evidence_requested_filter == 'yes':
        qs = qs.filter(evidence_requested=True)
    elif evidence_requested_filter == 'no':
        qs = qs.filter(evidence_requested=False)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(rank_name__icontains=q) | 
            Q(target__icontains=q) | 
            Q(indicator__icontains=q) | 
            Q(procedure__icontains=q) |
            Q(code__icontains=q) |
            Q(executor__icontains=q) |
            Q(comments__icontains=q) |
            Q(evaluation_notes__icontains=q) |
            Q(evidence_source_employee__icontains=q)
        ).distinct()
    
    # --- Dropdown options (based on the filtered queryset 'qs') ---
    all_years = qs.values_list('year', flat=True).distinct().order_by('year')
    all_rank_names = qs.values_list('rank_name', flat=True).distinct().order_by('rank_name')
    all_executors = qs.values_list('executor', flat=True).distinct().order_by('executor')
    all_date_ranges = qs.values_list('date_range', flat=True).distinct().order_by('date_range')
    all_follow_ups = qs.values_list('follow_up', flat=True).distinct().order_by('follow_up')
    all_evaluations = qs.values_list('evaluation', flat=True).distinct().order_by('evaluation')
    
    sort_by = request.GET.get('sort_by', 'rank_name')
    if sort_by == 'rank_name_exact':
        sort_by = 'rank_name'
    
    # Check if sort_by is a valid field to avoid errors
    valid_sort_fields = [
        'rank_name', 'target_no', 'indicator_no', 'procedure_no', 
        'target', 'executor', 'date_range', 'follow_up', 
        'evaluation', 'status', 'evidence_source_employee', 'code'
    ]
    if sort_by not in valid_sort_fields:
        sort_by = 'rank_name'

    qs = qs.order_by(f'{"-" if request.GET.get("sort_order") == "desc" else ""}{sort_by}')

    # --- Pagination Logic ---
    per_page = request.GET.get('per_page', '25')
    
    if per_page == 'all':
        # Show all items (no pagination)
        page_obj = qs
        # Mock paginator object for template compatibility
        class MockPaginator:
            count = qs.count()
            num_pages = 1
        page_obj.paginator = MockPaginator()
        page_obj.start_index = 1
        page_obj.end_index = qs.count()
        page_obj.has_previous = False
        page_obj.has_next = False
        page_obj.number = 1
    else:
        try:
            per_page = int(per_page)
            if per_page < 1: per_page = 25
        except ValueError:
            per_page = 25

        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(request.GET.get('page'))

    # --- Prepare Pagination URL Params ---
    # Safely remove 'page' from GET params to avoid 'cut' filter issues in template
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_url_params = query_params.urlencode()

    # Re-calculate roles based on WHOLE plan items
    is_executor_role = OperationalPlanItems.objects.filter(executor_committee__in=user_committees).exists()
    is_evaluator_role = OperationalPlanItems.objects.filter(evaluator_committee__in=user_committees).exists()

    # --- Role-Based Filter Redirection ---
    # If a user is only an evaluator but tries to view 'executor' tab (or lands there by default),
    # and they have 0 items in executor but many in evaluator, we should switch them.
    if is_evaluator_role and not is_executor_role and (not view_role or view_role == 'executor'):
        view_role = 'evaluator'
    
    if not view_role:
        view_role = 'executor'
    
    context = {
        'page_obj': page_obj,
        'user_committees': user_committees,
        'is_executor_role': is_executor_role,
        'is_evaluator_role': is_evaluator_role,
        
        # Pass filter values back to template to maintain state
        'q': q,
        'year': year,
        'rank_name_filter': rank_name,
        'executor_filter': executor,
        'date_range_filter': date_range,
        'follow_up_filter': follow_up,
        'evaluation_filter': evaluation,
        'status_filter': status_filter,
        'evidence_requested_filter': evidence_requested_filter,
        'sort_by': sort_by,
        'sort_order': request.GET.get('sort_order'),
        'per_page': str(per_page),
        'view_role': view_role,
        
        'pagination_url_params': pagination_url_params, # New clean params string

        # Dropdown options
        'all_years': all_years,
        'all_rank_names': all_rank_names,
        'all_executors': all_executors,
        'all_date_ranges': all_date_ranges,
        'all_follow_ups': all_follow_ups,
        'all_evaluations': all_evaluations,
        'all_statuses': OperationalPlanItems._meta.get_field('status').choices,
    }

    # HTMX Handling: return a partial only when the table container is the target.
    # This keeps sidebar navigation swaps stable (content-area) while preserving fast table updates.
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'plan-table-container':
        return render(request, 'plan/_table.html', context)

    return render(request, 'plan/list.html', context)

@login_required
def plan_edit_modal(request, pk:int):
    """
    This view is now clean and no longer handles file lists.
    """
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    
    evaluators = []
    try:
        quality_committee = Group.objects.get(name='لجنة الجودة والتخطيط')
        if hasattr(quality_committee, 'extension'):
            ext = quality_committee.extension
            axis_mapping = {
                ext.axis1_name: ext.axis1_evaluators,
                ext.axis2_name: ext.axis2_evaluators,
                ext.axis3_name: ext.axis3_evaluators,
                ext.axis4_name: ext.axis4_evaluators,
                ext.axis5_name: ext.axis5_evaluators,
                ext.axis6_name: ext.axis6_evaluators,
            }
            evaluator_users = axis_mapping.get(item.rank_name)
            if evaluator_users:
                evaluators = [user.staff_profile.name for user in evaluator_users.all() if hasattr(user, 'staff_profile')]
    except (Group.DoesNotExist, AttributeError):
        pass

    # Pass the user to the form to filter evidence files
    form = PlanItemExecutionForm(instance=item, user=request.user)
    context = {
        'item': item,
        'form': form,
        'evaluator_name': ", ".join(evaluators) if evaluators else "غير محدد"
    }
    return render(request, 'plan/_modal_edit.html', context)

@login_required
def plan_edit_save(request, pk:int):
    """
    This view is now clean and no longer handles file lists.
    """
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    user_committees = request.user.committees.all()
    
    # Permission Check: Superusers can always edit
    if request.user.is_superuser:
        pass
    else:
        is_executor = item.executor_committee in user_committees
        # Allow edit if not completed
        if not is_executor or item.status == 'Completed':
            return HttpResponseForbidden("ليس لديك الصلاحية لتعديل هذا البند في حالته الحالية.")
    
    if request.method == 'POST':
        # Pass the user to the form to validate evidence files
        form = PlanItemExecutionForm(request.POST, instance=item, user=request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            
            # Explicitly save fields from the form
            instance.status = form.cleaned_data.get('status', instance.status)
            instance.follow_up = form.cleaned_data.get('follow_up', instance.follow_up)
            instance.evidence_type = form.cleaned_data.get('evidence_type', instance.evidence_type)
            instance.evidence_source_file = form.cleaned_data.get('evidence_source_file', instance.evidence_source_file)
            instance.evidence_document = form.cleaned_data.get('evidence_document', instance.evidence_document)
            instance.comments = form.cleaned_data.get('comments', instance.comments)

            instance.save()
            form.save_m2m() # For ManyToMany fields, if any in this form

            # IMPORTANT: Reload the instance to ensure all related objects and updated fields are fresh
            # Use select_related and prefetch_related to optimize queries for the template
            instance = OperationalPlanItems.objects.select_related(
                'academic_year', 'strategic_goal_link', 'operational_goal_link',
                'executor_committee', 'evaluator_committee', 'evidence_document'
            ).get(pk=pk)
            
            resp = render(request, 'plan/_row.html', {
                'it': instance,
                'user_committees': user_committees, # Pass committees to redraw buttons correctly
                'request': request
            })
            resp['HX-Trigger'] = json.dumps({'closeModal': True, 'showMessage': {'level': 'success', 'message': 'تم الحفظ بنجاح'}})
            return resp
        context = {'item': item, 'form': form}
        return render(request, 'plan/_modal_edit.html', context, status=422)
    return HttpResponse(status=405)

# ... (Evaluation views are unchanged and correct) ...
@login_required
def plan_evaluate_modal(request, pk:int):
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    
    evaluators = []
    try:
        quality_committee = Group.objects.get(name='لجنة الجودة والتخطيط')
        if hasattr(quality_committee, 'extension'):
            ext = quality_committee.extension
            axis_mapping = {
                ext.axis1_name: ext.axis1_evaluators,
                ext.axis2_name: ext.axis2_evaluators,
                ext.axis3_name: ext.axis3_evaluators,
                ext.axis4_name: ext.axis4_evaluators,
                ext.axis5_name: ext.axis5_evaluators,
                ext.axis6_name: ext.axis6_evaluators,
            }
            evaluator_users = axis_mapping.get(item.rank_name)
            if evaluator_users:
                evaluators = [user.staff_profile.name for user in evaluator_users.all() if hasattr(user, 'staff_profile')]
    except (Group.DoesNotExist, AttributeError):
        pass

    # Set the evaluator name automatically but allow override if needed (though user said read only name)
    form = PlanItemEvaluationForm(instance=item, initial={
        'evaluation_notes': "",
        'evidence_source_employee': ", ".join(evaluators) if evaluators else "غير محدد"
    })
    
    context = {
        'item': item, 
        'form': form, 
        'evaluation_options': ["مطابق", "غير مطابق", "مطابق جزئي"],
        'evaluator_name': ", ".join(evaluators) if evaluators else "غير محدد"
    }
    return render(request, 'plan/_modal_evaluate.html', context)

@login_required
def plan_evaluate_save(request, pk:int):
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    user_committees = request.user.committees.all()
    
    # Permission Check
    is_evaluator = item.evaluator_committee in user_committees
    
    if not request.user.is_superuser and not is_evaluator:
        return HttpResponseForbidden("ليس لديك صلاحية تقييم هذا البند.")

    if request.method == 'POST':
        form = PlanItemEvaluationForm(request.POST, instance=item)
        if form.is_valid():
            # Save the data from the form to the instance
            item.status = form.cleaned_data.get('status', item.status)
            item.evaluation = form.cleaned_data.get('evaluation', item.evaluation)
            item.evaluation_notes = form.cleaned_data.get('evaluation_notes', item.evaluation_notes)
            item.evidence_requested = form.cleaned_data.get('evidence_requested', item.evidence_requested)
            item.evidence_request_note = form.cleaned_data.get('evidence_request_note', item.evidence_request_note)
            
            # Set the evaluator name from the current user
            try:
                staff_profile = Staff.objects.get(user=request.user)
                item.evidence_source_employee = staff_profile.job_title.title if staff_profile.job_title else request.user.username
            except Staff.DoesNotExist:
                item.evidence_source_employee = request.user.username

            # Set the review date
            item.last_review_date = timezone.now()
            
            # Save the instance to the database
            item.save()
            
            # Re-fetch user committees for context
            user_committees = request.user.committees.all()
            
            context = {
                'it': item,
                'user_committees': user_committees,
                'view_role': 'evaluator',
                'request': request
            }
            
            resp = render(request, 'plan/_row.html', context)
            resp['HX-Trigger'] = json.dumps({
                'closeModal': True, 
                'showMessage': {'level': 'success', 'message': 'تم اعتماد التقييم بنجاح'}
            })
            return resp
        
        # If invalid, re-render modal with errors
        context = {
            'item': item, 
            'form': form, 
            'evaluation_options': ["مطابق", "غير مطابق", "مطابق جزئي"],
            'evaluator_name': request.POST.get('evidence_source_employee', '')
        }
        return render(request, 'plan/_modal_evaluate.html', context, status=422)
    return HttpResponse(status=405)

@login_required
def plan_toggle_evidence_request(request, pk:int):
    """
    Toggles the evidence_requested flag via AJAX/HTMX from the table row.
    """
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    user_committees = request.user.committees.all()
    
    # Permission Check
    if not request.user.is_superuser and item.evaluator_committee not in user_committees:
        return HttpResponseForbidden("ليس لديك صلاحية تعديل هذا البند.")
        
    if request.method == 'POST':
        item.evidence_requested = not item.evidence_requested
        if item.evidence_requested:
            item.evidence_requested_at = timezone.now()
            item.status = 'Pending Review' # Ensure it's not completed if more evidence is needed
        item.save()
        
        # Return the updated row to reflect the state change
        context = {
            'it': item,
            'user_committees': user_committees,
            'view_role': 'evaluator',
            'request': request
        }
        return render(request, 'plan/_row.html', context)
    
    return HttpResponse(status=405)


@login_required
def plan_upload_evidence_modal(request, pk:int):
    """
    Shows a specialized modal to upload a new evidence file for a requested item.
    """
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    form = EvidenceUploadForm(initial={'title': f"دليل: {item.procedure[:50]}"})
    
    context = {
        'item': item,
        'form': form,
    }
    return render(request, 'plan/_modal_upload_evidence.html', context)

@login_required
def plan_upload_evidence_save(request, pk:int):
    """
    Saves the uploaded evidence, creates a document in the vault, and links it to the item.
    """
    item = get_object_or_404(OperationalPlanItems, pk=pk)
    user_committees = request.user.committees.all()
    
    if request.method == 'POST':
        form = EvidenceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Create the EvidenceDocument in the Vault
            doc = form.save(commit=False)
            doc.user = request.user
            doc.academic_year = item.academic_year
            
            # Use current year for academic year if item has none
            if not doc.academic_year:
                from ..models import AcademicYear
                doc.academic_year = AcademicYear.objects.filter(is_active=True).first()
            
            doc.save() # File is handled by ModelForm if 'file' field is in Meta.fields or handled manually
            
            # 2. Link it to the Plan Item
            item.evidence_document = doc
            item.status = 'Pending Review' # Update status to indicate something happened
            # IMPORTANT: We do NOT clear evidence_requested here.
            # This allows the Evaluator to see the "View Evidence" link in their column
            # instead of the "Request Evidence" button reverting back.
            item.save()
            
            # 3. Return updated row
            resp = render(request, 'plan/_row.html', {
                'it': item,
                'user_committees': user_committees,
                'request': request
            })
            resp['HX-Trigger'] = json.dumps({'closeModal': True, 'showMessage': {'level': 'success', 'message': 'تم رفع الدليل بنجاح وتقديمه للمراجعة'}})
            return resp
            
        context = {'item': item, 'form': form}
        return render(request, 'plan/_modal_upload_evidence.html', context, status=422)
    return HttpResponse(status=405)