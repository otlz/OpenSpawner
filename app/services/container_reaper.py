"""Background-Job: stoppt inaktive Container, räumt veraltete auf."""
from datetime import datetime, timedelta
from sqlalchemy import or_
from app.extensions import db
from app.models import UserContainer
from app.services.container_manager import ContainerManager
from config import Config


class ContainerReaper:
    """Reaper-Klasse für regelmäßige Container-Bereinigung via APScheduler."""

    def __init__(self, app):
        self.app = app

    def reap_idle_containers(self):
        """Stoppt Container, die länger als CONTAINER_IDLE_TIMEOUT inaktiv sind.

        Wird alle REAPER_INTERVAL Sekunden aufgerufen.
        """
        with self.app.app_context():
            timeout = Config.CONTAINER_IDLE_TIMEOUT
            cutoff = datetime.utcnow() - timedelta(seconds=timeout)

            idle_containers = UserContainer.query.filter(
                UserContainer.status == 'running',
                or_(UserContainer.last_used < cutoff, UserContainer.last_used.is_(None)),
                UserContainer.is_blocked == False,
                UserContainer.container_id.isnot(None)
            ).all()

            if not idle_containers:
                return

            manager = ContainerManager()
            stopped = 0
            changed = False

            for uc in idle_containers:
                try:
                    status = manager.get_container_status(uc.container_id)
                    if status == 'running':
                        manager.stop_container(uc.container_id)
                        uc.status = 'stopped'
                        stopped += 1
                        changed = True
                        self.app.logger.info(
                            f"[REAPER] Stopped idle container {uc.container_id[:12]} "
                            f"(type={uc.container_type}, user={uc.user_id})"
                        )
                    elif status == 'not_found':
                        uc.status = 'not_created'
                        uc.container_id = None
                        changed = True
                    elif status == 'stopped':
                        uc.status = 'stopped'
                        changed = True
                except Exception as e:
                    self.app.logger.warning(
                        f"[REAPER] Failed to stop container {uc.container_id[:12]}: {str(e)}"
                    )

            if changed:
                db.session.commit()
            if stopped:
                self.app.logger.info(f"[REAPER] Stopped {stopped} idle containers")

    def reap_stale_containers(self):
        """Entfernt gestoppte Container, die länger als CONTAINER_STALE_TIMEOUT inaktiv sind.

        Volumes werden NICHT gelöscht — nur der Container wird entfernt.
        Beim nächsten Launch wird ein neuer Container erstellt, Volumes bleiben erhalten.

        Wird stündlich aufgerufen.
        """
        with self.app.app_context():
            timeout = Config.CONTAINER_STALE_TIMEOUT
            cutoff = datetime.utcnow() - timedelta(seconds=timeout)

            stale_containers = UserContainer.query.filter(
                UserContainer.status == 'stopped',
                UserContainer.last_used < cutoff,
                UserContainer.container_id.isnot(None)
            ).all()

            if not stale_containers:
                return

            manager = ContainerManager()
            removed = 0

            for uc in stale_containers:
                try:
                    manager.remove_container(uc.container_id)
                    old_id = uc.container_id[:12]
                    uc.container_id = None
                    uc.container_port = None
                    uc.status = 'not_created'
                    removed += 1
                    self.app.logger.info(
                        f"[REAPER] Removed stale container {old_id} "
                        f"(type={uc.container_type}, user={uc.user_id}, volumes preserved)"
                    )
                except Exception as e:
                    self.app.logger.warning(
                        f"[REAPER] Failed to remove stale container {uc.container_id[:12]}: {str(e)}"
                    )

            if removed:
                db.session.commit()
                self.app.logger.info(f"[REAPER] Removed {removed} stale containers (volumes preserved)")
