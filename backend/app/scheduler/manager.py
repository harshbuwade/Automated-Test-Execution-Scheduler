import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.models.enums import ScheduleType
from app.models.schedule import Schedule

logger = logging.getLogger("test_scheduler.manager")


def build_apscheduler_trigger(schedule_type: ScheduleType, schedule_expression: str) -> Any:
    """Builds an APScheduler trigger from ScheduleType and expression.

    Raises ValueError if expression format is invalid.
    """
    expr = schedule_expression.strip()
    if not expr:
        raise ValueError("Schedule expression cannot be blank.")

    if schedule_type == ScheduleType.INTERVAL:
        try:
            seconds = int(expr)
            if seconds <= 0:
                raise ValueError("Interval must be a positive integer greater than 0.")
            return IntervalTrigger(seconds=seconds, timezone=timezone.utc)
        except ValueError as exc:
            if "positive" in str(exc) or "blank" in str(exc):
                raise
            raise ValueError(f"Invalid interval expression '{expr}'. Must be an integer number of seconds.") from exc

    elif schedule_type == ScheduleType.CRON:
        try:
            return CronTrigger.from_crontab(expr, timezone=timezone.utc)
        except Exception as exc:
            raise ValueError(f"Invalid cron expression '{expr}'. Must be a valid 5-field cron string.") from exc
    else:
        raise ValueError(f"Unsupported schedule type '{schedule_type}'.")


def calculate_next_run(schedule_type: ScheduleType, schedule_expression: str) -> Optional[datetime]:
    """Calculates next run datetime in UTC based on schedule configuration."""
    try:
        trigger = build_apscheduler_trigger(schedule_type, schedule_expression)
        now = datetime.now(timezone.utc)
        return trigger.get_next_fire_time(previous_fire_time=None, now=now)
    except Exception:
        return None


from apscheduler.schedulers.base import STATE_STOPPED, STATE_RUNNING


class SchedulerManager:
    """Singleton Manager handling APScheduler background job lifecycle."""

    def __init__(self):
        self._init_scheduler()

    def _init_scheduler(self):
        self.scheduler = BackgroundScheduler(
            timezone=timezone.utc,
            job_defaults={
                "max_instances": 1,
                "coalesce": True,
                "misfire_grace_time": 60,
            },
        )
        self._is_running = False

    def start(self):
        """Starts the APScheduler background thread."""
        if self.scheduler.state == STATE_STOPPED:
            self._init_scheduler()

        if not self._is_running or self.scheduler.state != STATE_RUNNING:
            self.scheduler.start(paused=False)
            self._is_running = True
            logger.info("APScheduler started successfully.")


    def shutdown(self, wait: bool = False):
        """Shuts down the APScheduler background thread."""
        if self._is_running:
            self.scheduler.shutdown(wait=wait)
            self._is_running = False
            logger.info("APScheduler stopped successfully.")

    def get_job_id(self, schedule_id: int) -> str:
        return f"schedule_{schedule_id}"

    def remove_schedule_job(self, schedule_id: int):
        """Removes an APScheduler job if registered."""
        job_id = self.get_job_id(schedule_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id} from APScheduler.")

    def add_or_update_schedule_job(
        self,
        schedule: Schedule,
        job_func: Callable[..., Any],
    ):
        """Registers or replaces an APScheduler job for an active schedule."""
        job_id = self.get_job_id(schedule.id)

        # Remove existing job first
        self.remove_schedule_job(schedule.id)

        if not schedule.is_active:
            logger.info(f"Schedule {schedule.id} is inactive. Job not registered.")
            return

        trigger = build_apscheduler_trigger(schedule.schedule_type, schedule.schedule_expression)

        self.scheduler.add_job(
            func=job_func,
            trigger=trigger,
            id=job_id,
            name=f"Schedule_{schedule.id}_Test_{schedule.test_id}",
            args=[schedule.test_id, schedule.id],
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        logger.info(f"Registered job {job_id} for test_id={schedule.test_id}.")

    def load_active_schedules_on_startup(
        self,
        db_factory: Callable[[], Any],
        job_func: Callable[..., Any],
    ):
        """Loads active schedules from database on server startup and registers APScheduler jobs."""
        db = db_factory()
        try:
            active_schedules = (
                db.query(Schedule)
                .filter(Schedule.is_active == True)  # noqa: E712
                .all()
            )
            logger.info(f"Loading {len(active_schedules)} active schedules on startup...")
            for sched in active_schedules:
                try:
                    self.add_or_update_schedule_job(sched, job_func)
                    sched.next_run = calculate_next_run(sched.schedule_type, sched.schedule_expression)
                except Exception as exc:
                    logger.error(f"Failed to register startup schedule {sched.id}: {exc}")
            db.commit()
        finally:
            db.close()


scheduler_manager = SchedulerManager()
