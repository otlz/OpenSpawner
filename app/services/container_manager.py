"""Container-Verwaltung für Docker-basierte Benutzer-Container."""
import ipaddress
import logging
import re
import socket
import time
import docker
from config import Config

logger = logging.getLogger(__name__)

FIREWALL_CONTAINER = 'openspawner-egress-firewall'
# Opt-in compose service of the same firewall in earlier versions
LEGACY_FIREWALL_CONTAINER = 'egress-firewall'

# Without a limit a user can fill the host's disk through the container log
# (writing to /proc/1/fd/1 works for the container's own user)
USER_LOG_CONFIG = docker.types.LogConfig(
    type='json-file', config={'max-size': '10m', 'max-file': '3'}
)


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

    def image_exists(self, image_name: str) -> bool:
        """Prüft ob ein Docker-Image lokal vorhanden ist."""
        try:
            self._get_client().images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False
        except Exception:
            return False

    def get_available_images(self) -> set:
        """Gibt ein Set aller lokal verfügbaren Image-Tags zurück."""
        try:
            images = self._get_client().images.list()
            tags = set()
            for img in images:
                tags.update(img.tags or [])
            return tags
        except Exception:
            return set()

    def _build_traefik_labels(self, user_id, slug, container_type=None):
        """Erstellt Traefik-Routing-Labels für einen Benutzer-Container."""
        base_host = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"
        router_name = f"user{user_id}" if not container_type else f"user{user_id}-{container_type}"
        path_slug = slug if not container_type else f"{slug}-{container_type}"

        # linuxserver.io images serve under SUBFOLDER themselves and need the full path
        template = Config.CONTAINER_TEMPLATES.get(container_type) or {}
        strip_prefix = template.get('strip_prefix', True)

        # Auth runs first (sees the unstripped path), then the prefix is stripped
        middlewares = [f'{router_name}-auth', f'{router_name}-noindex']
        if strip_prefix:
            middlewares.append(f'{router_name}-strip')

        labels = {
            'traefik.enable': 'true',
            'traefik.docker.network': self._user_network_name(user_id),

            f'traefik.http.routers.{router_name}.rule':
                f'Host(`{base_host}`) && PathPrefix(`/{path_slug}`)',
            f'traefik.http.routers.{router_name}.entrypoints': Config.TRAEFIK_ENTRYPOINT,
            f'traefik.http.routers.{router_name}.priority': '100',
            f'traefik.http.routers.{router_name}.service': router_name,
            f'traefik.http.routers.{router_name}.middlewares': ','.join(middlewares),
            # User apps live on the school's official host: keep them out of search engines
            f'traefik.http.middlewares.{router_name}-noindex.headers.customresponseheaders.X-Robots-Tag':
                'noindex, nofollow',
            f'traefik.http.middlewares.{router_name}-auth.forwardauth.address': Config.FORWARD_AUTH_URL,
            # Traefik sets X-Forwarded-Uri itself; never trust a client-supplied one
            f'traefik.http.middlewares.{router_name}-auth.forwardauth.trustForwardHeader': 'false',
            f'traefik.http.routers.{router_name}.tls': 'true',
            f'traefik.http.routers.{router_name}.tls.certresolver': Config.TRAEFIK_CERTRESOLVER,
            f'traefik.http.services.{router_name}.loadbalancer.server.port': '8080',
        }
        if strip_prefix:
            labels[f'traefik.http.middlewares.{router_name}-strip.stripprefix.prefixes'] = f'/{path_slug}'
        return labels

    @staticmethod
    def _user_network_name(user_id):
        """Name des eigenen Netzwerks eines Benutzers (Traefik-Modus)."""
        return f"spawner-user{user_id}"

    @staticmethod
    def _user_subnet(user_id):
        """Fester /28-Block pro Benutzer aus USER_NETWORK_SUBNET.

        Explicit subnets: Docker's default address pools only hold about 30
        networks, and every compose project on the host already takes one.
        """
        pool = ipaddress.ip_network(Config.USER_NETWORK_SUBNET)
        if user_id >= pool.num_addresses // 16:
            raise Exception(f"USER_NETWORK_SUBNET {pool} has no room for user {user_id}")
        return ipaddress.ip_network((int(pool.network_address) + user_id * 16, 28))

    def _find_traefik_container(self):
        """Findet den Traefik-Container, der OpenSpawner routet.

        Returns:
            (container_id, uses_host_network)
        """
        api = self._get_client().api
        if Config.TRAEFIK_CONTAINER:
            info = api.inspect_container(Config.TRAEFIK_CONTAINER)
            return info['Id'], info['HostConfig'].get('NetworkMode') == 'host'

        # The Traefik that routes our backend sits on TRAEFIK_NETWORK
        candidates = [
            c for c in api.containers(filters={'network': Config.TRAEFIK_NETWORK})
            if c.get('Image', '').split('@')[0].split(':')[0].split('/')[-1] == 'traefik'
            or (c.get('Labels') or {}).get('org.opencontainers.image.title', '').lower() == 'traefik'
        ]
        if len(candidates) != 1:
            raise Exception(
                f"Found {len(candidates)} Traefik containers on '{Config.TRAEFIK_NETWORK}', "
                "set TRAEFIK_CONTAINER"
            )
        return candidates[0]['Id'], candidates[0]['HostConfig'].get('NetworkMode') == 'host'

    def _ensure_user_network(self, user_id):
        """Erstellt das eigene Netzwerk eines Benutzers und hängt Traefik an.

        Only the user's containers and Traefik share it: no other users, no
        backend, none of the other apps on the Traefik network.
        """
        client = self._get_client()
        name = self._user_network_name(user_id)
        try:
            network = client.networks.get(name)
        except docker.errors.NotFound:
            try:
                network = client.networks.create(
                    name,
                    driver='bridge',
                    ipam=docker.types.IPAMConfig(
                        pool_configs=[docker.types.IPAMPool(subnet=str(self._user_subnet(user_id)))]
                    ),
                    labels={'spawner.managed': 'true', 'spawner.user_id': str(user_id)},
                )
                logger.info(f"[SPAWNER] Network {name} created")
            except docker.errors.APIError:
                # Created concurrently by a parallel launch of the same user
                network = client.networks.get(name)

        traefik_id, host_network = self._find_traefik_container()
        if not host_network:
            network.reload()
            self._attach_traefik(network, traefik_id)
        return name

    @staticmethod
    def _attach_traefik(network, traefik_id):
        """Verbindet Traefik mit einem Benutzer-Netzwerk, falls noch nicht geschehen."""
        if traefik_id in (network.attrs.get('Containers') or {}):
            return False
        network.connect(traefik_id)
        logger.info(f"[SPAWNER] Traefik connected to {network.name}")
        return True

    def attach_traefik_to_user_networks(self):
        """Hängt Traefik an alle Benutzer-Netzwerke an.

        A recreated Traefik container (e.g. after a Dokploy update) loses these
        connections, which makes every running user container unreachable.

        Returns:
            Number of networks Traefik was attached to.
        """
        traefik_id, host_network = self._find_traefik_container()
        if host_network:
            return 0
        networks = self._get_client().networks.list(
            filters={'label': 'spawner.user_id'}, greedy=True
        )
        return sum(self._attach_traefik(network, traefik_id) for network in networks)

    def remove_user_network(self, user_id):
        """Entfernt das Netzwerk eines Benutzers (inkl. Traefik-Anbindung)."""
        try:
            network = self._get_client().networks.get(self._user_network_name(user_id))
        except docker.errors.NotFound:
            return
        for container_id in list(network.attrs.get('Containers') or {}):
            try:
                network.disconnect(container_id, force=True)
            except Exception as e:
                logger.warning(f"[SPAWNER] Could not disconnect {container_id[:12]}: {str(e)}")
        network.remove()
        logger.info(f"[SPAWNER] Network {network.name} removed")

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

    def _get_container_network(self, user_id):
        """Netzwerk, mit dem der Container erstellt wird (None = Docker-Standard-Bridge).

        Traefik mode: the user's own network (see _ensure_user_network).
        Local mode: falls back to the default bridge, the published port is enough.
        """
        if Config.TRAEFIK_ENABLED:
            return self._ensure_user_network(user_id)
        try:
            self._get_client().networks.get(Config.CONTAINER_NETWORK)
            return Config.CONTAINER_NETWORK
        except docker.errors.NotFound:
            logger.warning(
                f"[SPAWNER] Network '{Config.CONTAINER_NETWORK}' not found, using default bridge"
            )
            return None

    def _get_assigned_port(self, container):
        """Liest den vom Docker zugewiesenen Host-Port für Port 8080 aus."""
        container.reload()
        ports = container.ports.get('8080/tcp')
        if ports and len(ports) > 0:
            return int(ports[0]['HostPort'])
        return None

    @staticmethod
    def _build_volume_name(user_id, container_type, name_suffix):
        """Builds a named Docker volume name for a user container."""
        return f"spawner-user{user_id}-{container_type}-{name_suffix}"

    def _build_volumes(self, user_id, container_type, volume_specs):
        """Builds named Docker volumes dict from template volume specs.

        Args:
            user_id: The user's ID
            container_type: Template type (e.g. 'vcoder', 'dictionary')
            volume_specs: List of {'name_suffix': str, 'mount_path': str} from templates.json

        Returns:
            Dict for Docker SDK containers.run() volumes parameter, or None if no volumes.
        """
        if not volume_specs:
            return None

        volumes = {}
        for spec in volume_specs:
            vol_name = self._build_volume_name(user_id, container_type, spec['name_suffix'])
            volumes[vol_name] = {'bind': spec['mount_path'], 'mode': 'rw'}
            logger.info(f"[SPAWNER]   Volume: {vol_name} -> {spec['mount_path']}")

        return volumes

    def start_container(self, container_id):
        """Startet einen gestoppten Benutzer-Container."""
        try:
            container = self._get_client().containers.get(container_id)
            if container.status != 'running':
                container.start()
                logger.info(f"[SPAWNER] Container {container_id[:12]} started")
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

    def remove_volumes(self, user_id, container_type, volume_specs):
        """Entfernt alle Named Volumes eines Benutzer-Containers.

        Args:
            user_id: The user's ID
            container_type: Template type
            volume_specs: List of volume specs from template config
        """
        if not volume_specs:
            return

        client = self._get_client()
        for spec in volume_specs:
            vol_name = self._build_volume_name(user_id, container_type, spec['name_suffix'])
            try:
                volume = client.volumes.get(vol_name)
                volume.remove(force=True)
                logger.info(f"[SPAWNER] Volume {vol_name} removed")
            except docker.errors.NotFound:
                pass
            except Exception as e:
                logger.warning(f"[SPAWNER] Could not remove volume {vol_name}: {str(e)}")

    def ensure_egress_firewall(self, cleanup=False):
        """Startet die Egress-Firewall oder hält sie aktuell (Traefik-Modus).

        Runs app.services.egress_firewall from the backend's own image, so every
        deploy updates it. Called on startup and every REAPER_INTERVAL: a stopped
        or outdated firewall is replaced. Its rules stay in place meanwhile.

        Started here and not as a compose service: a host-network service fails
        the whole deploy when the platform adds networks to every service.

        Args:
            cleanup: With EGRESS_FIREWALL off, also remove rules that were left
                behind without a container (on startup).

        Returns:
            'running', 'started' or 'disabled'
        """
        client = self._get_client()
        self._remove_legacy_firewall(client)
        try:
            current = client.containers.get(FIREWALL_CONTAINER)
        except docker.errors.NotFound:
            current = None

        image = self._firewall_image()
        command = ['python', '-m', 'app.services.egress_firewall']
        options = {
            'network_mode': 'host',
            'user': '0',
            'cap_drop': ['ALL'],
            'cap_add': ['NET_ADMIN', 'NET_RAW'],
            'security_opt': ['no-new-privileges:true'],
            'mem_limit': '128m',
            'pids_limit': 32,
            'labels': {'openspawner.role': 'egress-firewall'},
            'log_config': docker.types.LogConfig(
                type='json-file', config={'max-size': '1m', 'max-file': '2'}
            ),
        }

        if not Config.EGRESS_FIREWALL:
            if current is not None or cleanup:
                if current is not None:
                    current.remove(force=True)
                client.containers.run(image, [*command, 'remove'], remove=True, **options)
                logger.warning(
                    "[SPAWNER] Egress firewall disabled (EGRESS_FIREWALL=false): "
                    "user containers reach the host and the LAN"
                )
            return 'disabled'

        env = {
            'USER_NETWORK_SUBNET': Config.USER_NETWORK_SUBNET,
            'EGRESS_ALLOW': Config.EGRESS_ALLOW,
            'TRAEFIK_CONTAINER': self._traefik_name(current),
            'DOCKER_HOST': 'unix:///var/run/docker.sock',
        }
        wanted = {f"{key}={value}" for key, value in env.items()}
        if (
            current is not None
            and current.status == 'running'
            and current.attrs.get('Image') == image
            and wanted <= set(current.attrs['Config'].get('Env') or [])
        ):
            return 'running'

        if current is not None:
            current.remove(force=True)
        client.containers.run(
            image,
            command,
            name=FIREWALL_CONTAINER,
            detach=True,
            restart_policy={'Name': 'unless-stopped'},
            environment=env,
            # Only to read Traefik's addresses (":ro" does not limit the API)
            volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'ro'}},
            **options,
        )
        logger.info(f"[SPAWNER] Egress firewall started for {Config.USER_NETWORK_SUBNET}")
        return 'started'

    @staticmethod
    def _remove_legacy_firewall(client):
        """Entfernt den Firewall-Compose-Dienst früherer Versionen (gleiche Ketten)."""
        try:
            legacy = client.containers.get(LEGACY_FIREWALL_CONTAINER)
        except docker.errors.NotFound:
            return
        if legacy.attrs['Config'].get('Image', '').startswith('openspawner-egress-firewall'):
            legacy.remove(force=True)
            logger.info("[SPAWNER] Removed the egress-firewall service of an earlier version")

    def _firewall_image(self):
        """ID des Images, aus dem die Firewall läuft: das eigene des Backends."""
        client = self._get_client()
        if Config.EGRESS_FIREWALL_IMAGE:
            return client.images.get(Config.EGRESS_FIREWALL_IMAGE).id
        for ref in (socket.gethostname(), self._own_container_id()):
            if not ref:
                continue
            try:
                return client.containers.get(ref).attrs['Image']
            except docker.errors.APIError:
                continue
        raise Exception("Own container not found, set EGRESS_FIREWALL_IMAGE")

    @staticmethod
    def _own_container_id():
        """Container-ID aus den Mounts (falls der Hostname gesetzt wurde)."""
        try:
            with open('/proc/self/mountinfo') as f:
                match = re.search(r'/containers/([0-9a-f]{64})/', f.read())
        except OSError:
            return None
        return match.group(1) if match else None

    def _traefik_name(self, current):
        """Name des Traefik-Containers, dessen Adressen die Firewall sperrt."""
        try:
            traefik_id, host_network = self._find_traefik_container()
            if host_network:
                return ''
            return self._get_client().api.inspect_container(traefik_id)['Name'].lstrip('/')
        except Exception as e:
            # Traefik may be restarting: keep what the running firewall uses
            if current is not None:
                for item in current.attrs['Config'].get('Env') or []:
                    if item.startswith('TRAEFIK_CONTAINER='):
                        return item.split('=', 1)[1]
            logger.warning(f"[SPAWNER] Traefik not found for the egress firewall: {e}")
            return ''

    def purge_user_resources(self, user_id):
        """Entfernt alle Container, Volumes und das Netzwerk einer Benutzer-ID.

        SQLite gives the ID of a deleted newest user to the next signup, and
        volumes are named by ID: anything left behind (files, GitHub logins)
        would go to the next student. Works from labels and name prefixes, not
        the DB records: those miss volumes kept by a container delete and
        templates removed from the catalog.

        Raises on failure, so callers can refuse to hand out the ID.

        Returns:
            Number of containers removed.
        """
        client = self._get_client()
        containers = client.containers.list(
            all=True, filters={'label': f'spawner.user_id={user_id}'}
        )
        for container in containers:
            container.remove(force=True)
            logger.info(f"[SPAWNER] Container {container.name} purged")

        # Docker's name filter is a substring match, hence the startswith
        prefix = f"spawner-user{user_id}-"
        for volume in client.volumes.list(filters={'name': prefix}):
            if volume.name.startswith(prefix):
                volume.remove(force=True)
                logger.info(f"[SPAWNER] Volume {volume.name} purged")

        self.remove_user_network(user_id)
        return len(containers)

    def remove_outdated_containers(self):
        """Entfernt Benutzer-Container mit veralteten Traefik-Labels (Traefik-Modus).

        Labels are fixed at creation, a restart keeps them. This catches
        containers from before owner-only access (no login, old SECRET_KEY in
        env), before per-user networks (on the shared Traefik network) and any
        later routing change. Volumes are kept, the next launch creates a
        fresh container.

        Returns:
            Number of containers removed.
        """
        removed = 0
        containers = self._get_client().containers.list(
            all=True, filters={'label': 'spawner.user_id'}
        )
        for container in containers:
            labels = container.labels
            expected = self._build_traefik_labels(
                labels['spawner.user_id'],
                labels.get('spawner.slug', ''),
                labels.get('spawner.container_type'),
            )
            current = {k: v for k, v in labels.items() if k.startswith('traefik.')}
            if current != expected:
                container.remove(force=True)
                removed += 1
                logger.info(f"[SPAWNER] Removed outdated container {container.name}")
        return removed

    def wait_until_listening(self, container_id, port=8080, timeout=20):
        """Wartet bis im Container ein Prozess auf dem Port lauscht.

        Reads /proc/net/tcp inside the container, so it works without network
        access to the isolated user network and without curl in the image.
        """
        container = self._get_client().containers.get(container_id)
        local_port = f":{port:04X}"
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = container.exec_run(['cat', '/proc/net/tcp', '/proc/net/tcp6'])
            for line in result.output.decode(errors='ignore').splitlines():
                fields = line.split()
                # local_address ends with the hex port, state 0A = LISTEN
                if len(fields) > 3 and fields[1].endswith(local_port) and fields[3] == '0A':
                    return True
            time.sleep(0.5)
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

    def remove_old_containers(self, user_id, container_type):
        """Entfernt alte Container des gleichen Typs für einen Benutzer.

        Used by ContainerOrchestrator.recreate() to prevent Traefik router conflicts.
        """
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
                        logger.info(f"[SPAWNER] Old container {old_container.name} stopped")
                    except Exception as e:
                        logger.warning(f"[SPAWNER] Could not stop old container: {str(e)}")
                try:
                    old_container.remove(force=True)
                    logger.info(f"[SPAWNER] Old container {old_container.name} removed (conflict prevention)")
                except Exception as e:
                    logger.warning(f"[SPAWNER] Could not remove old container: {str(e)}")
        except Exception as e:
            logger.warning(f"[SPAWNER] Error removing old containers: {str(e)}")

    def spawn_container(self, user_id, slug, container_type):
        """
        Erstellt einen neuen Container für einen Benutzer.

        Does NOT remove old containers — that's the orchestrator's responsibility.

        Returns:
            (container_id, container_port)
        """
        try:
            template = Config.CONTAINER_TEMPLATES.get(container_type)
            if not template:
                raise ValueError(f"Invalid container type: {container_type}")

            image = template['image']
            container_name = f"user-{slug}-{container_type}-{user_id}"

            # Build labels
            labels = self._build_metadata_labels(user_id, slug, container_type)
            if Config.TRAEFIK_ENABLED:
                labels.update(self._build_traefik_labels(user_id, slug, container_type))

            logger.info(f"[SPAWNER] Creating {container_type} container {container_name}")
            logger.info(f"[SPAWNER] Image: {image}")
            if Config.TRAEFIK_ENABLED:
                logger.info(f"[SPAWNER] Traefik Labels:")
                for key, value in labels.items():
                    if 'traefik' in key:
                        logger.info(f"[SPAWNER]   {key}: {value}")

            # Build named volumes from template config
            volumes = self._build_volumes(user_id, container_type, template.get('volumes', []))

            # Environment variables for container. Never pass secrets here: users
            # have a shell in many templates and can read the environment.
            env_vars = {
                'USER_ID': str(user_id),
                'USER_SLUG': slug,
                'CONTAINER_TYPE': container_type,
            }

            # linuxserver.io images need SUBFOLDER for reverse-proxy path prefixes
            if Config.TRAEFIK_ENABLED:
                path_slug = f"{slug}-{container_type}"
                env_vars['SUBFOLDER'] = f"/{path_slug}/"

            # Port mapping for local mode (no Traefik)
            ports = {'8080/tcp': None} if not Config.TRAEFIK_ENABLED else None

            # Per-template resource limits
            memory_limit = template.get('memory_limit', Config.DEFAULT_MEMORY_LIMIT)
            cpu_quota = template.get('cpu_quota', Config.DEFAULT_CPU_QUOTA)
            pids_limit = template.get('pids_limit', 100)

            # Security: minimal capabilities
            base_caps = ['CHOWN', 'SETUID', 'SETGID', 'NET_BIND_SERVICE']
            extra_caps = template.get('cap_add', [])
            cap_add = list(set(base_caps + extra_caps))

            container = self._get_client().containers.run(
                image=image,
                name=container_name,
                detach=True,
                labels=labels,
                environment=env_vars,
                restart_policy={'Name': 'no'},
                mem_limit=memory_limit,
                cpu_quota=cpu_quota,
                pids_limit=pids_limit,
                cap_drop=['ALL'],
                cap_add=cap_add,
                security_opt=['no-new-privileges:true'],
                log_config=USER_LOG_CONFIG,
                volumes=volumes,
                ports=ports,
                # Attach at creation, not via network.connect() afterwards: a
                # container that briefly sits on the default bridge can be picked
                # up by Traefik with its bridge IP (unreachable, 504), and the
                # default bridge is shared with every other container on the host
                network=self._get_container_network(user_id),
            )

            # Warte bis Container bereit ist
            logger.info(f"[SPAWNER] Waiting for container startup...")
            startup_wait = getattr(Config, 'CONTAINER_STARTUP_WAIT', 2)
            max_retries = 30
            retry_count = 0
            while retry_count < max_retries:
                try:
                    container.reload()
                    if container.status == 'running':
                        logger.info(f"[SPAWNER] Container running, waiting {startup_wait}s for service startup...")
                        time.sleep(startup_wait)
                        logger.info(f"[SPAWNER] Container ready!")
                        break
                except Exception as e:
                    logger.warning(f"[SPAWNER] Error during status check: {str(e)}")

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
                logger.info(f"[SPAWNER] {container_type.upper()} container created: {container.id[:12]}")
                logger.info(f"[SPAWNER] URL: {Config.PREFERRED_URL_SCHEME}://{base_host}/{slug_with_suffix}")
                return container.id, 8080
            else:
                host_port = self._get_assigned_port(container)
                logger.info(f"[SPAWNER] {container_type.upper()} container created: {container.id[:12]}")
                logger.info(f"[SPAWNER] URL: http://localhost:{host_port}")
                return container.id, host_port or 8080

        except docker.errors.ImageNotFound:
            error_msg = f"Template image '{template['image']}' for type '{container_type}' not found"
            logger.error(f"[SPAWNER] {error_msg}")
            raise Exception(error_msg)
        except docker.errors.APIError as e:
            error_msg = f"Docker API error: {str(e)}"
            logger.error(f"[SPAWNER] {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"[SPAWNER] {str(e)}")
            raise

    # Backward compatibility alias
    spawn_multi_container = spawn_container
