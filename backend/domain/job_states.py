"""
Single source of truth for what counts as terminal at the Job level.
WAITING_APPROVAL is explicitly NOT terminal - a job paused for human
review is still an active, resumable job, not a finished one.
"""
JOB_TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "CANCELLED"})