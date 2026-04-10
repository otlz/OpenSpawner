"""High-level Container-Lifecycle-Management.

Wraps ContainerManager with business logic: ensure_running, stop, restart, recreate, destroy.
"""
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import UserContainer
from app.services.container_manager import ContainerManager
from config import Config


class ContainerOrchestrator:
    """Orchestriert Container-Lifecycle: start, stop, restart, recreate, destroy."""

    def __init__(self):
        self.manager = ContainerManager()

    def ensure_running(self, user, container_type):
        """Stellt sicher, dass ein Container läuft. Startet gestoppte, erstellt fehlende.

        Returns:
            (user_container, created: bool) — the UserContainer record and whether it was newly created.
        """
        template = Config.CONTAINER_TEMPLATES.get(container_type)
        if not template:
            raise ValueError(f"Invalid container type: {container_type}")

        user_container = UserContainer.query.filter_by(
            user_id=user.id,
            container_type=container_type
        ).first()

        if user_container and user_container.container_id:
            status = self.manager.get_container_status(user_container.container_id)

            if status == 'running':
                user_container.last_used = datetime.utcnow()
                db.session.commit()
                return user_container, False

            if status == 'stopped':
                if self.manager.start_container(user_container.container_id):
                    user_container.last_used = datetime.utcnow()
                    user_container.status = 'running'
                    db.session.commit()
                    current_app.logger.info(
                        f"[ORCHESTRATOR] Container {user_container.container_id[:12]} resumed for {user.email}"
                    )
                    return user_container, False

            # Container not_found or start failed — recreate
            current_app.logger.warning(
                f"[ORCHESTRATOR] Container {user_container.container_id[:12]} unavailable (status={status}), recreating"
            )
            self.manager.remove_old_containers(user.id, container_type)
            container_id, port = self.manager.spawn_container(user.id, user.slug, container_type)
            user_container.container_id = container_id
            user_container.container_port = port
            user_container.last_used = datetime.utcnow()
            user_container.status = 'running'
            db.session.commit()
            return user_container, False

        # No container record or no container_id — create new
        self.manager.remove_old_containers(user.id, container_type)
        container_id, port = self.manager.spawn_container(user.id, user.slug, container_type)

        if user_container:
            user_container.container_id = container_id
            user_container.container_port = port
            user_container.last_used = datetime.utcnow()
            user_container.status = 'running'
        else:
            user_container = UserContainer(
                user_id=user.id,
                container_type=container_type,
                container_id=container_id,
                container_port=port,
                template_image=template['image'],
                last_used=datetime.utcnow(),
                status='running'
            )
            db.session.add(user_container)

        db.session.commit()
        current_app.logger.info(
            f"[ORCHESTRATOR] Container {container_type} created for {user.email}"
        )
        return user_container, True

    def stop(self, user_container):
        """Stoppt einen Container (preserves state and data).

        Returns:
            True if stopped successfully.
        """
        if not user_container.container_id:
            return False

        result = self.manager.stop_container(user_container.container_id)
        if result:
            user_container.status = 'stopped'
            db.session.commit()
        return result

    def restart(self, user_container):
        """Docker restart (stop + start, NO recreate). Preserves container state.

        Returns:
            True if restarted successfully, False if fallback to recreate is needed.
        """
        if not user_container.container_id:
            return False

        try:
            container = self.manager._get_client().containers.get(user_container.container_id)
            container.restart(timeout=10)
            user_container.last_used = datetime.utcnow()
            user_container.status = 'running'
            db.session.commit()
            return True
        except Exception:
            return False

    def recreate(self, user, user_container):
        """Full destroy + recreate (for image updates or broken containers).

        Returns:
            (container_id, container_port)
        """
        container_type = user_container.container_type

        # Stop and remove old container
        if user_container.container_id:
            try:
                self.manager.stop_container(user_container.container_id)
            except Exception:
                pass
            try:
                self.manager.remove_container(user_container.container_id)
            except Exception:
                pass

        # Clean up any orphans
        self.manager.remove_old_containers(user.id, container_type)

        # Spawn new container
        container_id, port = self.manager.spawn_container(user.id, user.slug, container_type)
        user_container.container_id = container_id
        user_container.container_port = port
        user_container.last_used = datetime.utcnow()
        user_container.status = 'running'
        db.session.commit()

        current_app.logger.info(
            f"[ORCHESTRATOR] Container {container_type} recreated for {user.email}"
        )
        return container_id, port

    def destroy(self, user_container, delete_volumes=False):
        """Entfernt einen Container und optional seine Volumes.

        Returns:
            True if destroyed successfully.
        """
        if user_container.container_id:
            try:
                self.manager.stop_container(user_container.container_id)
            except Exception:
                pass
            try:
                self.manager.remove_container(user_container.container_id)
            except Exception:
                pass

        if delete_volumes:
            template = Config.CONTAINER_TEMPLATES.get(user_container.container_type, {})
            volume_specs = template.get('volumes', [])
            self.manager.remove_volumes(
                user_container.user_id,
                user_container.container_type,
                volume_specs
            )

        db.session.delete(user_container)
        db.session.commit()
        return True

    def stop_all_for_user(self, user):
        """Stoppt alle laufenden Container eines Benutzers (Logout-Hook).

        Returns:
            Number of containers stopped.
        """
        stopped = 0
        for uc in user.containers:
            if uc.container_id:
                try:
                    status = self.manager.get_container_status(uc.container_id)
                    if status == 'running':
                        self.manager.stop_container(uc.container_id)
                        uc.status = 'stopped'
                        stopped += 1
                except Exception as e:
                    current_app.logger.warning(
                        f"[ORCHESTRATOR] Failed to stop container {uc.container_id[:12]}: {str(e)}"
                    )
        if stopped:
            db.session.commit()
        return stopped
