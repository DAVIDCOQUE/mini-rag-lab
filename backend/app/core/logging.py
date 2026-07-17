import logging


def configure_logging() -> None:
    """Configura el logging basico en consola para toda la aplicacion."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
