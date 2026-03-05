"""
Push Notification Service (Phase 11.4)
======================================
Handles device token management, notification preferences, and push alert
dispatch for mobile clients (iOS / Android).

Push delivery is simulated when FCM_SERVER_KEY / APNS credentials are not
configured.  When credentials are present the service is ready to integrate
with Firebase Admin SDK (FCM) or Apple Push Notification service (APNs).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.entities.mobile import DeviceToken, NotificationPreference
from backend.models.entities.user import User
from backend.core.config import settings


class PushNotificationService:

    # ── Device Token Management ────────────────────────────────────────────

    @staticmethod
    def register_device(
        db: Session, user: User, platform: str, token: str
    ) -> DeviceToken:
        """Register a new device token for a user."""
        if platform not in ["ios", "android"]:
            raise HTTPException(status_code=400, detail="Invalid platform. Must be 'ios' or 'android'.")

        device = db.query(DeviceToken).filter(DeviceToken.token == token).first()

        if device:
            device.user_id = user.id
            device.platform = platform
            device.is_active = True
            device.last_used_at = datetime.utcnow()
        else:
            device = DeviceToken(
                user_id=user.id,
                platform=platform,
                token=token,
                is_active=True,
                last_used_at=datetime.utcnow()
            )
            db.add(device)

        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def unregister_device(db: Session, user: User, token: str) -> None:
        """Unregister a device token."""
        device = db.query(DeviceToken).filter(
            DeviceToken.token == token,
            DeviceToken.user_id == user.id
        ).first()

        if not device:
            raise HTTPException(status_code=404, detail="Device token not found.")

        device.is_active = False
        db.commit()

    @staticmethod
    def get_user_tokens(db: Session, user_id: str) -> List[str]:
        """Get all active tokens for a user."""
        devices = db.query(DeviceToken).filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        ).all()
        return [d.token for d in devices]

    # ── Notification Preferences ───────────────────────────────────────────

    @staticmethod
    def get_preferences(db: Session, user_id: str) -> NotificationPreference:
        """Get (or create default) notification preferences for a user."""
        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(
        db: Session,
        user_id: str,
        votes_enabled: Optional[bool] = None,
        alerts_enabled: Optional[bool] = None,
        tasks_enabled: Optional[bool] = None,
        constitutional_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
    ) -> NotificationPreference:
        """Update notification preferences for a user."""
        pref = PushNotificationService.get_preferences(db, user_id)
        if votes_enabled is not None:
            pref.votes_enabled = votes_enabled
        if alerts_enabled is not None:
            pref.alerts_enabled = alerts_enabled
        if tasks_enabled is not None:
            pref.tasks_enabled = tasks_enabled
        if constitutional_enabled is not None:
            pref.constitutional_enabled = constitutional_enabled
        if quiet_hours_start is not None:
            pref.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            pref.quiet_hours_end = quiet_hours_end
        db.commit()
        db.refresh(pref)
        return pref

    # ── Push Dispatch ──────────────────────────────────────────────────────

    @staticmethod
    def send_push(db: Session, user_id: str, title: str, body: str, data: Optional[dict] = None) -> int:
        """
        Send a generic push notification to a user.
        Returns the number of devices targeted.
        """
        tokens = PushNotificationService.get_user_tokens(db, user_id)
        if not tokens:
            return 0

        # In production, integrate with Firebase Admin SDK (FCM) or APNs here.
        # if settings.FCM_SERVER_KEY:
        #    message = messaging.MulticastMessage(...)
        #    response = messaging.send_multicast(message)

        print(f"[PUSH NOTIFICATION] Sent to {len(tokens)} devices for user {user_id}. Title: {title}")
        return len(tokens)

    @staticmethod
    def send_vote_alert(db: Session, user_id: str, vote_data: Dict[str, Any]) -> int:
        """Send a push notification for a new vote. Respects notification preferences."""
        pref = PushNotificationService.get_preferences(db, user_id)
        if not pref.votes_enabled:
            return 0
        title = "New Vote Initiated"
        body = vote_data.get("description", "A new vote requires your attention.")
        return PushNotificationService.send_push(db, user_id, title, body, data=vote_data)

    @staticmethod
    def send_constitutional_alert(db: Session, user_id: str, alert_data: Dict[str, Any]) -> int:
        """Send a push for a constitutional violation alert. Respects notification preferences."""
        pref = PushNotificationService.get_preferences(db, user_id)
        if not pref.constitutional_enabled:
            return 0
        severity = alert_data.get("severity", "WARNING")
        title = f"Constitutional Alert ({severity})"
        body = alert_data.get("message", "A constitutional event occurred.")
        return PushNotificationService.send_push(db, user_id, title, body, data=alert_data)

    @staticmethod
    def send_task_update(db: Session, user_id: str, task_data: Dict[str, Any]) -> int:
        """Send a push for a task status change. Respects notification preferences."""
        pref = PushNotificationService.get_preferences(db, user_id)
        if not pref.tasks_enabled:
            return 0
        task_status = task_data.get("status", "updated")
        title = f"Task {task_status.capitalize()}"
        body = task_data.get("description", "A task has been updated.")[:100]
        return PushNotificationService.send_push(db, user_id, title, body, data=task_data)

    # ── Maintenance ────────────────────────────────────────────────────────

    @staticmethod
    def cleanup_stale_tokens(db: Session, days_stale: int = 180) -> int:
        """Mark tokens as inactive if they haven't been used recently."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_stale)
        stale_devices = db.query(DeviceToken).filter(
            DeviceToken.is_active == True,
            DeviceToken.last_used_at < cutoff_date
        ).all()

        for device in stale_devices:
            device.is_active = False

        if stale_devices:
            db.commit()

        return len(stale_devices)
