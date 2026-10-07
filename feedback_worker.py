"""One local worker; no Streamlit calls or learner text in process-wide job keys."""

import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import feedback_store
import separate_feedback


class FeedbackWorker:
    def __init__(self):
        self.pool = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="speakwell-grammar"
        )
        self.active = set()
        self.lock = Lock()

    def start(self, job):
        key = job["job_id"]
        with self.lock:
            if key in self.active:
                return
            self.active.add(key)
        try:
            self.pool.submit(self._run, dict(job))
        except RuntimeError:
            with self.lock:
                self.active.discard(key)

    def _run(self, job):
        try:
            feedback_store.run_job(job, separate_feedback.grammar_feedback)
        except Exception as exc:  # noqa: BLE001 -- UI reports unavailable after storage failure
            logging.getLogger(__name__).warning(
                "Grammar job storage failure: %s", type(exc).__name__
            )
        finally:
            with self.lock:
                self.active.discard(job["job_id"])

    def is_active(self, job_id):
        with self.lock:
            return job_id in self.active

    def close(self):
        self.pool.shutdown(wait=True)
