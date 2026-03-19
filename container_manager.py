import requests_unixsocket
import docker
from config import Config

class ContainerManager:
    def __init__(self):
        self.client = None

    def _get_client(self):
        """Lazy initialization of Docker client"""
        if self.client is None:
            try:
                # Nutze from_env() - DOCKER_HOST aus Umgebungsvariable
                self.client = docker.from_env()

            except Exception as e:
                raise Exception(f"Docker connection failed: {str(e)}")
        return self.client
    
    def spawn_container(self, user_id, slug):
        """Spawnt einen neuen Container für den User"""
        try:
            existing = self._get_user_container(slug)
            if existing and existing.status == 'running':
                return existing.id, self._get_container_port(existing)

            # Pfad-basiertes Routing: User unter coder.domain.org/<slug>
            base_host = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"

            # Labels vorbereiten
            labels = {
                'traefik.enable': 'true',
                'traefik.docker.network': Config.TRAEFIK_NETWORK,

                # HTTPS Router mit PathPrefix
                f'traefik.http.routers.user{user_id}.rule':
                    f'Host(`{base_host}`) && PathPrefix(`/{slug}`)',
                f'traefik.http.routers.user{user_id}.entrypoints': Config.TRAEFIK_ENTRYPOINT,
                f'traefik.http.routers.user{user_id}.priority': '100',
                # Router muss zum Service zeigen
                f'traefik.http.routers.user{user_id}.service': f'user{user_id}',
                # StripPrefix Middleware - entfernt /{slug} bevor Container Request erhält
                f'traefik.http.routers.user{user_id}.middlewares': f'user{user_id}-strip',
                f'traefik.http.middlewares.user{user_id}-strip.stripprefix.prefixes': f'/{slug}',
                # TLS für HTTPS
                f'traefik.http.routers.user{user_id}.tls': 'true',
                f'traefik.http.routers.user{user_id}.tls.certresolver': Config.TRAEFIK_CERTRESOLVER,

                # Service mit Port-Konfiguration
                f'traefik.http.services.user{user_id}.loadbalancer.server.port': '8080',

                # Metadata
                'spawner.user_id': str(user_id),
                'spawner.slug': slug,
                'spawner.managed': 'true'
            }

            # Logging: Traefik-Labels ausgeben
            print(f"[SPAWNER] Creating container user-{slug}-{user_id}")
            print(f"[SPAWNER] Traefik Labels:")
            for key, value in labels.items():
                if 'traefik' in key:
                    print(f"[SPAWNER]   {key}: {value}")

            container = self._get_client().containers.run(
                Config.USER_TEMPLATE_IMAGE,
                name=f"user-{slug}-{user_id}",
                detach=True,
                labels=labels,
                environment={
                    'USER_ID': str(user_id),
                    'USER_SLUG': slug,
                    'JWT_SECRET': Config.SECRET_KEY  # Für Token-Validierung im Container
                },
                restart_policy={'Name': 'unless-stopped'},
                mem_limit=Config.DEFAULT_MEMORY_LIMIT,
                cpu_quota=Config.DEFAULT_CPU_QUOTA
            )

            # Container an Traefik-Netzwerk verbinden
            try:
                network = self._get_client().networks.get(Config.TRAEFIK_NETWORK)
                network.connect(container)
                print(f"[SPAWNER] Container an Netzwerk '{Config.TRAEFIK_NETWORK}' verbunden")
            except Exception as e:
                print(f"[SPAWNER] WARNUNG: Container konnte nicht an Netzwerk verbunden werden: {str(e)}")
                container.remove(force=True)
                raise Exception(f"Konnte Container nicht an Netzwerk '{Config.TRAEFIK_NETWORK}' verbinden: {str(e)}")

            print(f"[SPAWNER] Container created: {container.id[:12]}")
            print(f"[SPAWNER] URL: https://{base_host}/{slug}")
            return container.id, 8080
            
        except docker.errors.ImageNotFound as e:
            error_msg = f"Template-Image '{Config.USER_TEMPLATE_IMAGE}' nicht gefunden"
            print(f"[SPAWNER] ERROR: {error_msg}")
            raise Exception(error_msg)
        except docker.errors.APIError as e:
            error_msg = f"Docker API Fehler: {str(e)}"
            print(f"[SPAWNER] ERROR: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"[SPAWNER] ERROR: {str(e)}")
            raise
    
    def start_container(self, container_id):
        """Startet einen gestoppten User-Container"""
        try:
            container = self._get_client().containers.get(container_id)
            if container.status != 'running':
                container.start()
                print(f"[SPAWNER] Container {container_id[:12]} gestartet")
            return True
        except docker.errors.NotFound:
            return False

    def stop_container(self, container_id):
        """Stoppt einen User-Container"""
        try:
            container = self._get_client().containers.get(container_id)
            container.stop(timeout=10)
            return True
        except docker.errors.NotFound:
            return False
    
    def remove_container(self, container_id):
        """Entfernt einen User-Container komplett"""
        try:
            container = self._get_client().containers.get(container_id)
            container.remove(force=True)
            return True
        except docker.errors.NotFound:
            return False
    
    def get_container_status(self, container_id):
        """Gibt Status eines Containers zurück"""
        try:
            container = self._get_client().containers.get(container_id)
            return container.status
        except docker.errors.NotFound:
            return 'not_found'
    
    def _get_user_container(self, slug):
        """Findet existierenden Container für User"""
        filters = {'label': f'spawner.slug={slug}'}
        containers = self._get_client().containers.list(all=True, filters=filters)
        return containers[0] if containers else None
    
    def _get_container_port(self, container):
        """Extrahiert Port aus Container-Config"""
        return 8080

    def spawn_multi_container(self, user_id: int, slug: str, container_type: str) -> tuple:
        """
        Spawnt einen Container für einen User mit bestimmtem Typ

        Args:
            user_id: User ID
            slug: User Slug (für URL)
            container_type: 'dev' oder 'prod'

        Returns:
            (container_id, container_port)
        """
        try:
            # Template-Config holen
            template = Config.CONTAINER_TEMPLATES.get(container_type)
            if not template:
                raise ValueError(f"Ungültiger Container-Typ: {container_type}")

            image = template['image']
            container_name = f"user-{slug}-{container_type}-{user_id}"

            # Traefik Labels mit Suffix
            slug_with_suffix = f"{slug}-{container_type}"
            base_host = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"

            labels = {
                'traefik.enable': 'true',
                'traefik.docker.network': Config.TRAEFIK_NETWORK,

                # HTTPS Router mit PathPrefix
                f'traefik.http.routers.user{user_id}-{container_type}.rule':
                    f'Host(`{base_host}`) && PathPrefix(`/{slug_with_suffix}`)',
                f'traefik.http.routers.user{user_id}-{container_type}.entrypoints': Config.TRAEFIK_ENTRYPOINT,
                f'traefik.http.routers.user{user_id}-{container_type}.priority': '100',
                # Router muss zum Service zeigen
                f'traefik.http.routers.user{user_id}-{container_type}.service': f'user{user_id}-{container_type}',
                # StripPrefix Middleware - entfernt /{slug_with_suffix} bevor Container Request erhält
                f'traefik.http.routers.user{user_id}-{container_type}.middlewares': f'user{user_id}-{container_type}-strip',
                f'traefik.http.middlewares.user{user_id}-{container_type}-strip.stripprefix.prefixes': f'/{slug_with_suffix}',
                # TLS für HTTPS
                f'traefik.http.routers.user{user_id}-{container_type}.tls': 'true',
                f'traefik.http.routers.user{user_id}-{container_type}.tls.certresolver': Config.TRAEFIK_CERTRESOLVER,

                # Service mit Port-Konfiguration
                f'traefik.http.services.user{user_id}-{container_type}.loadbalancer.server.port': '8080',

                # Metadata
                'spawner.user_id': str(user_id),
                'spawner.slug': slug,
                'spawner.container_type': container_type,
                'spawner.managed': 'true'
            }

            # Lösche ALLE alten Container mit gleicher user_id und container_type (B)
            # Dies verhindert Traefik Router-Konflikte mit mehreren Containern gleicher Config
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
                            print(f"[SPAWNER] Alter Container {old_container.name} gestoppt")
                        except Exception as e:
                            print(f"[SPAWNER] WARNUNG: Kann alten Container nicht stoppen: {str(e)}")
                    try:
                        old_container.remove(force=True)
                        print(f"[SPAWNER] Alter Container {old_container.name} gelöscht (Traefik-Konflikt-Prävention)")
                    except Exception as e:
                        print(f"[SPAWNER] WARNUNG: Kann alten Container nicht löschen: {str(e)}")
            except Exception as e:
                print(f"[SPAWNER] WARNUNG: Fehler beim Löschen alter Container: {str(e)}")

            # Logging: Traefik-Labels ausgeben
            print(f"[SPAWNER] Creating {container_type} container user-{slug}-{container_type}-{user_id}")
            print(f"[SPAWNER] Image: {image}")
            print(f"[SPAWNER] Traefik Labels:")
            for key, value in labels.items():
                if 'traefik' in key:
                    print(f"[SPAWNER]   {key}: {value}")

            container = self._get_client().containers.run(
                image=image,
                name=container_name,
                detach=True,
                labels=labels,
                environment={
                    'USER_ID': str(user_id),
                    'USER_SLUG': slug,
                    'CONTAINER_TYPE': container_type,
                    'JWT_SECRET': Config.SECRET_KEY  # Für Token-Validierung im Container
                },
                restart_policy={'Name': 'unless-stopped'},
                mem_limit=Config.DEFAULT_MEMORY_LIMIT,
                cpu_quota=Config.DEFAULT_CPU_QUOTA
            )

            # Container an Traefik-Netzwerk verbinden
            try:
                network = self._get_client().networks.get(Config.TRAEFIK_NETWORK)
                network.connect(container)
                print(f"[SPAWNER] Container an Netzwerk '{Config.TRAEFIK_NETWORK}' verbunden")
            except Exception as e:
                print(f"[SPAWNER] WARNUNG: Container konnte nicht an Netzwerk verbunden werden: {str(e)}")
                container.remove(force=True)
                raise Exception(f"Konnte Container nicht an Netzwerk '{Config.TRAEFIK_NETWORK}' verbinden: {str(e)}")

            print(f"[SPAWNER] {container_type.upper()} container created: {container.id[:12]}")
            print(f"[SPAWNER] URL: {Config.PREFERRED_URL_SCHEME}://{base_host}/{slug_with_suffix}")
            return container.id, 8080

        except docker.errors.ImageNotFound as e:
            error_msg = f"Template-Image '{template['image']}' für Typ '{container_type}' nicht gefunden"
            print(f"[SPAWNER] ERROR: {error_msg}")
            raise Exception(error_msg)
        except docker.errors.APIError as e:
            error_msg = f"Docker API Fehler: {str(e)}"
            print(f"[SPAWNER] ERROR: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"[SPAWNER] ERROR: {str(e)}")
            raise
