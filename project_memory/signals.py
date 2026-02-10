from django.contrib.admin.models import LogEntry
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MemoryEvent

@receiver(post_save, sender=LogEntry)
def log_admin_action(sender, instance, created, **kwargs):
    """
    A signal receiver that listens to new LogEntry objects and creates
    a MemoryEvent for each one.
    """
    if created:
        MemoryEvent.objects.create(
            event_type='ADMIN_ACTION',
            description=f"إجراء إداري: '{instance.get_change_message()}' على كائن '{instance.object_repr}'.",
            details={
                'object_id': instance.object_id,
                'content_type_id': instance.content_type_id,
                'action_flag': instance.action_flag,
            },
            related_user=instance.user,
            is_significant=False # Admin actions are usually not architecturally significant
        )