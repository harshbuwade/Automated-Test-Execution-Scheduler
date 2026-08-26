"""Sample timeout pytest script."""
import time


def test_sample_timeout():
    """Sleeps to trigger execution engine timeout."""
    time.sleep(10)
