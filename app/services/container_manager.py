"""Container-Verwaltung für Docker-basierte Benutzer-Container."""
import time
import docker
from config import Config


class ContainerManager:
    """Verwaltet Docker-Container für Benutzer (erstellen, starten, stoppen, löschen)."""

    def __init__(self):
        self.client = None

    def _get_client(self):
        """Lazy-Initialisierung des Docker-Clients."""
        if self.client is None:
            try:
                self.client = docker.from_env()
            except Exception as e:
                raise Exception(f"Docker connection failed: {str(e)}")
        return self.client

    def _build_traefik_labels(self, user_id, slug, container_type=None):
        """Erstellt Traefik-Routing-Labels für einen Benutzer-Container."""
        base_host = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"
        router_name = f"user{user_id}" if not container_type else f"user{user_id}-{container_type}"
        path_slug = slug if not container_type else f"{slug}-{container_type}"

        return {
            'traefik.enable': 'true',
            'traefik.docker.network': Config.TRAEFIK_NETWORK,

            f'traefik.http.routers.{router_name}.rule':
                f'Host(`{base_host}`) && PathPrefix(`/{path_slug}`)',
            f'traefik.http.routers.{router_name}.entrypoints': Config.TRAEFIK_ENTRYPOINT,
            f'traefik.http.routers.{router_name}.priority': '100',
            f'traefik.http.routers.{router_name}.service': router_name,
            f'traefik.http.routers.{router_name}.middlewares': f'{router_name}-strip',
            f'traefik.http.middlewares.{router_name}-strip.stripprefix.prefixes': f'/{path_slug}',
            f'traefik.http.routers.{router_name}.tls': 'true',
            f'traefik.http.routers.{router_name}.tls.certresolver': Config.TRAEFIK_CERTRESOLVER,
            f'traefik.http.services.{router_name}.loadbalancer.server.port': '8080',
        }

    def _build_metadata_labels(self, user_id, slug, container_type=None):
        """Erstellt Spawner-Metadaten-Labels für Container-Zuordnung."""
        labels = {
            'spawner.user_id': str(user_id),
            'spawner.slug': slug,
            'spawner.managed': 'true'
        }
        if container_type:
            labels['spawner.container_type'] = container_type
        return labels

    def _connect_container_to_network(self, container, network_name, fatal=True):
        """Verbindet einen Container mit dem angegebenen Docker-Netzwerk."""
        try:
            network = self._get_client().networks.get(network_name)
            network.connect(container)
            print(f"[SPAWNER] Container connected to network '{network_name}'")
        except Exception as e:
            print(f"[SPAWNER] WARNING: Could not connect container to network: {str(e)}")
            if fatal:
                container.remove(force=True)
                raise Exception(f"Could not connect container to network '{network_name}': {str(e)}")

    def _get_assigned_port(self, container):
        """Liest den vom Docker zugewiesenen Host-Port für Port 8080 aus."""
        container.reload()
        ports = container.ports.get('8080/tcp')
        if ports and len(ports) > 0:
            return int(ports[0]['HostPort'])
        return None

    def start_container(self, container_id):
        """Startet einen gestoppten Benutzer-Container."""
        try:
            container = self._get_client().containers.get(container_id)
            if container.status != 'running':
                container.start()
                print(f"[SPAWNER] Container {container_id[:12]} started")
            return True
        except docker.errors.NotFound:
            return False

    def stop_container(self, container_id):
        """Stoppt einen Benutzer-Container."""
        try:
            container = self._get_client().containers.get(container_id)
            container.stop(timeout=10)
            return True
        except docker.errors.NotFound:
            return False

    def remove_container(self, container_id):
        """Entfernt einen Benutzer-Container vollständig."""
        try:
            container = self._get_client().containers.get(container_id)
            container.remove(force=True)
            return True
        except docker.errors.NotFound:
            return False

    def get_container_status(self, container_id):
        """Gibt den Status eines Containers zurück (running, stopped, not_found, etc.)."""
        try:
            container = self._get_client().containers.get(container_id)
            status = container.status
            if status == 'exited':
                return 'stopped'
            return status
        except docker.errors.NotFound:
            return 'not_found'

    def _get_user_container(self, slug):
        """Sucht einen existierenden Container anhand des User-Slugs."""
        filters = {'label': f'spawner.slug={slug}'}
        containers = self._get_client().containers.list(all=True, filters=filters)
        return containers[0] if containers else None

    def _get_container_port(self, container):
        """Ermittelt den Port eines Containers (Traefik: 8080, lokal: zugewiesener Port)."""
        if not Config.TRAEFIK_ENABLED:
            port = self._get_assigned_port(container)
            if port:
                return port
        return 8080

    def spawn_multi_container(self, user_id: int, slug: str, container_type: str) -> tuple:
        """
        Erstellt einen Container für einen Benutzer mit einem bestimmten Template-Typ.
        Entfernt vorher alte Container des gleichen Typs (Konflikt-Vermeidung).

        Returns:
            (container_id, container_port)
        """
        try:
            # Get template config
            template = Config.CONTAINER_TEMPLATES.get(container_type)
            if not template:
                raise ValueError(f"Invalid container type: {container_type}")

            image = template['image']
            container_name = f"user-{slug}-{container_type}-{user_id}"

            # Build labels
            labels = self._build_metadata_labels(user_id, slug, container_type)
            if Config.TRAEFIK_ENABLED:
                labels.update(self._build_traefik_labels(user_id, slug, container_type))

            # Remove old containers with same user_id and container_type
            # This prevents Traefik router conflicts with multiple containers
            try:
                filters = {
                    'label': [
                        f'spawner.user_id={user_id}',
                        f'spawner.container_type={container_type}'
                    ]
                }
                old_containers = self._get_client().containers.list(all=True, filters=filters)
                for old_container in old_containers:
                    if old_container.status == 'running':
                        try:
                            old_container.stop(timeout=5)
                            print(f"[SPAWNER] Old container {old_container.name} stopped")
                        except Exception as e:
                            print(f"[SPAWNER] WARNING: Could not stop old container: {str(e)}")
                    try:
                        old_container.remove(force=True)
                        print(f"[SPAWNER] Old container {old_container.name} removed (conflict prevention)")
                    except Exception as e:
                        print(f"[SPAWNER] WARNING: Could not remove old container: {str(e)}")
            except Exception as e:
                print(f"[SPAWNER] WARNING: Error removing old containers: {str(e)}")

            print(f"[SPAWNER] Creating {container_type} container {container_name}")
            print(f"[SPAWNER] Image: {image}")
            if Config.TRAEFIK_ENABLED:
                print(f"[SPAWNER] Traefik Labels:")
                for key, value in labels.items():
                    if 'traefik' in key:
                        print(f"[SPAWNER]   {key}: {value}")

            # Persistent volumes for specific container types
            volumes = {}
            if container_type == 'vcoder':
                data_path = f"/data/users/{user_id}/vcoder"
                volumes = {
                    f"{data_path}/workspace": {'bind': '/home/coder/project', 'mode': 'rw'},
                    f"{data_path}/platformio": {'bind': '/home/coder/.platformio', 'mode': 'rw'},
                }
                print(f"[SPAWNER] Volumes for vcoder:")
                for host, vol_config in volumes.items():
                    print(f"[SPAWNER]   {host} -> {vol_config['bind']}")

            # Environment variables for container
            env_vars = {
                'USER_ID': str(user_id),
                'USER_SLUG': slug,
                'CONTAINER_TYPE': container_type,
                'JWT_SECRET': Config.SECRET_KEY
            }

            # Port mapping for local mode (no Traefik)
            ports = {'8080/tcp': None} if not Config.TRAEFIK_ENABLED else None

            container = self._get_client().containers.run(
                image=image,
                name=container_name,
                detach=True,
                labels=labels,
                environment=env_vars,
                restart_policy={'Name': 'unless-stopped'},
                mem_limit=Config.DEFAULT_MEMORY_LIMIT,
                cpu_quota=Config.DEFAULT_CPU_QUOTA,
                volumes=volumes if volumes else None,
                ports=ports
            )

            # Connect to network
            network_name = Config.TRAEFIK_NETWORK if Config.TRAEFIK_ENABLED else Config.CONTAINER_NETWORK
            self._connect_container_to_network(container, network_name, fatal=Config.TRAEFIK_ENABLED)

            # Warte bis Container bereit ist
            print(f"[SPAWNER] Waiting for container startup...")
            startup_wait = getattr(Config, 'CONTAINER_STARTUP_WAIT', 2)
            max_retries = 30
            retry_count = 0
            while retry_count < max_retries:
                try:
                    container.reload()
                    if container.status == 'running':
                        print(f"[SPAWNER] Container running, waiting {startup_wait}s for service startup...")
                        time.sleep(startup_wait)
                        print(f"[SPAWNER] Container ready!")
                        break
                except Exception as e:
                    print(f"[SPAWNER] Error during status check: {str(e)}")

                retry_count += 1
                time.sleep(1)

            # Container konnte nicht gestartet werden — Fehler statt falsch-positiv
            if retry_count >= max_retries:
                container.remove(force=True)
                raise Exception(f"Container {container_name} not ready after {max_retries} retries")

            # Determine access port and URL
            if Config.TRAEFIK_ENABLED:
                base_host = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"
                slug_with_suffix = f"{slug}-{container_type}"
                print(f"[SPAWNER] {container_type.upper()} container created: {container.id[:12]}")
                print(f"[SPAWNER] URL: {Config.PREFERRED_URL_SCHEME}://{base_host}/{slug_with_suffix}")
                return container.id, 8080
            else:
                host_port = self._get_assigned_port(container)
                print(f"[SPAWNER] {container_type.upper()} container created: {container.id[:12]}")
                print(f"[SPAWNER] URL: http://localhost:{host_port}")
                return container.id, host_port or 8080

        except docker.errors.ImageNotFound:
            error_msg = f"Template image '{template['image']}' for type '{container_type}' not found"
            print(f"[SPAWNER] ERROR: {error_msg}")
            raise Exception(error_msg)
        except docker.errors.APIError as e:
            error_msg = f"Docker API error: {str(e)}"
            print(f"[SPAWNER] ERROR: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"[SPAWNER] ERROR: {str(e)}")
            raise
