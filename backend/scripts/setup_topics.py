import logging
import subprocess

logger = logging.getLogger(__name__)


def setup_topics():
    """
    Local-development bootstrap script to create ONLY the already-approved raw topic names.

    DEVELOPMENT CONFIG ONLY:
    We use partitions=3 here purely to validate deterministic partitioning locally.
    This must NOT imply that the production partition count is 3.
    Production partition counts, retention, and downstream topic topology remain OPEN.
    """
    topics = [
        "irochi.events.connection.v1",
        "irochi.events.dns.v1",
        "irochi.events.tls.v1"
    ]

    container_name = "irochi-redpanda"

    logger.info("Bootstrapping raw event topics (DEVELOPMENT CONFIG ONLY)...")

    failed = False
    for topic in topics:
        try:
            # We use subprocess to call `rpk` inside the Redpanda container.
            # This avoids adding an admin client dependency just for local setup.
            result = subprocess.run(
                [
                    "docker", "exec", container_name,
                    "rpk", "topic", "create", topic,
                    "-p", "3", # DEVELOPMENT CONFIG ONLY
                    "-r", "1"
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 or "already exists" in result.stdout.lower() or "already exists" in result.stderr.lower():
                logger.info(f"Topic {topic} is ready.")
            else:
                logger.error(f"Failed to create topic {topic}: {result.stderr}")
                failed = True
        except Exception as e:
            logger.error(f"Failed to execute docker command: {e}")
            failed = True

    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_topics()
