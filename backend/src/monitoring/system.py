"""System resource metrics collection."""
import psutil
import threading
import time
from typing import Optional

from src.monitoring.metrics import (
    system_cpu_usage,
    system_memory_usage,
    system_disk_usage,
)
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class SystemMetricsCollector:
    """Collects system resource metrics."""

    def __init__(self, interval: int = 30):
        """
        Initialize system metrics collector.

        Args:
            interval: Collection interval in seconds
        """
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """Start collecting system metrics."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        logger.info("System metrics collector started")

    def stop(self):
        """Stop collecting system metrics."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("System metrics collector stopped")

    def _collect_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                self._collect_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Failed to collect system metrics: {e}")
                time.sleep(self.interval)

    def _collect_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.used)

            # Disk usage
            disk = psutil.disk_usage("/")
            system_disk_usage.set(disk.used)

        except Exception as e:
            logger.warning(f"Error collecting system metrics: {e}")


# Global collector instance
system_metrics_collector = SystemMetricsCollector()
