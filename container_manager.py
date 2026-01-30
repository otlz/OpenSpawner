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
    
    def spawn_container(self, user_id, username):
        """Spawnt einen neuen Container für den User"""
        try:
            existing = self._get_user_container(username)
            if existing and existing.status == 'running':
                return existing.id, self._get_container_port(existing)

            # Pfad-basiertes Routing: User unter coder.wieland.org/username
            base_host = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"

            # Labels vorbereiten
            labels = {
                'traefik.enable': 'true',
                'traefik.docker.network': Config.TRAEFIK_NETWORK,

                # HTTPS Router mit PathPrefix
                f'traefik.http.routers.user{user_id}.rule':
                    f'Host(`{base_host}`) && PathPrefix(`/{username}`)',
                f'traefik.http.routers.user{user_id}.entrypoints': Config.TRAEFIK_ENTRYPOINT,
                f'traefik.http.routers.user{user_id}.priority': '100',
                # StripPrefix Middleware - entfernt /{username} bevor Container Request erhält
                f'traefik.http.routers.user{user_id}.middlewares': f'user{user_id}-strip',
                f'traefik.http.middlewares.user{user_id}-strip.stripprefix.prefixes': f'/{username}',
                # TLS für HTTPS
                f'traefik.http.routers.user{user_id}.tls': 'true',
                f'traefik.http.routers.user{user_id}.tls.certresolver': Config.TRAEFIK_CERTRESOLVER,

                # Service
                f'traefik.http.services.user{user_id}.loadbalancer.server.port': '8080',

                # Metadata
                'spawner.user_id': str(user_id),
                'spawner.username': username,
                'spawner.managed': 'true'
            }

            # Logging: Traefik-Labels ausgeben
            print(f"[SPAWNER] Creating container user-{username}-{user_id}")
            print(f"[SPAWNER] Traefik Labels:")
            for key, value in labels.items():
                if 'traefik' in key:
                    print(f"[SPAWNER]   {key}: {value}")

            container = self._get_client().containers.run(
                Config.USER_TEMPLATE_IMAGE,
                name=f"user-{username}-{user_id}",
                detach=True,
                network=Config.TRAEFIK_NETWORK,
                labels=labels,
                environment={
                    'USER_ID': str(user_id),
                    'USERNAME': username
                },
                restart_policy={'Name': 'unless-stopped'},
                mem_limit=Config.DEFAULT_MEMORY_LIMIT,
                cpu_quota=Config.DEFAULT_CPU_QUOTA
            )

            print(f"[SPAWNER] Container created: {container.id[:12]}")
            print(f"[SPAWNER] URL: https://{base_host}/{username}")
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
    
    def _get_user_container(self, username):
        """Findet existierenden Container für User"""
        filters = {'label': f'spawner.username={username}'}
        containers = self._get_client().containers.list(all=True, filters=filters)
        return containers[0] if containers else None
    
    def _get_container_port(self, container):
        """Extrahiert Port aus Container-Config"""
        return 8080
