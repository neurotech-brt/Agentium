"""
Celery configuration for Agentium background tasks.
Updated with Task Execution Architecture: Governance Alignment
"""
import os
from celery import Celery
from celery.signals import worker_ready

os.environ.setdefault('PYTHONPATH', '/app')

celery_app = Celery(
    'agentium',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    include=[
        'backend.services.tasks.task_executor',
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    beat_schedule_filename='/tmp/celerybeat-schedule',
    beat_scheduler='celery.beat.PersistentScheduler',
    broker_connection_retry_on_startup=True,
)

# Beat schedule - Task Execution Architecture Aligned
celery_app.conf.beat_schedule = {
    # Health checks
    'health-check-every-5-minutes': {
        'task': 'backend.services.tasks.task_executor.check_channel_health',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Channel maintenance
    'cleanup-old-messages-daily': {
        'task': 'backend.services.tasks.task_executor.cleanup_old_channel_messages',
        'schedule': 86400.0,  # 24 hours
        'kwargs': {'days': 30}
    },
    
    'imap-receiver-check': {
        'task': 'backend.services.tasks.task_executor.start_imap_receivers',
        'schedule': 60.0,  # Every minute
    },
    
    'channel-heartbeat': {
        'task': 'backend.services.tasks.task_executor.send_channel_heartbeat',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Constitution & idle tasks (existing)
    'constitution-daily-review': {
        'task': 'backend.services.tasks.task_executor.daily_constitution_review',
        'schedule': 86400.0,  # 24 hours
    },
    
    'idle-task-processor': {
        'task': 'backend.services.tasks.task_executor.process_idle_tasks',
        'schedule': 60.0,  # Every minute
    },
    
    # ═══════════════════════════════════════════════════════════
    # NEW: Task Execution Architecture Tasks
    # ═══════════════════════════════════════════════════════════
    
    # Self-Healing: Process escalated tasks (every 5 minutes)
    'handle-task-escalation': {
        'task': 'backend.services.tasks.task_executor.handle_task_escalation',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Data Retention: Daily sovereign cleanup
    'sovereign-data-retention': {
        'task': 'backend.services.tasks.task_executor.sovereign_data_retention',
        'schedule': 86400.0,  # Daily at midnight
    },
    
    # Auto-Scaling: Check queue depth every 10 minutes
    'auto-scale-check': {
        'task': 'backend.services.tasks.task_executor.auto_scale_check',
        'schedule': 600.0,  # 10 minutes
    },
}

@worker_ready.connect
def on_worker_ready(**kwargs):
    print("🥬 Celery worker ready for Agentium tasks")
    print("   Task Execution Architecture: Governance Alignment active")
    
    # Start IMAP receivers on worker startup
    from backend.services.tasks.task_executor import start_imap_receivers
    start_imap_receivers.delay()

if __name__ == '__main__':
    celery_app.start()