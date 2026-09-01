from django.urls import path
from presentation.api.sse import job_progress_stream
from presentation.api.views import AdjudicateView, CancelJobView, JobStatusView

urlpatterns = [
    path("adjudicate/", AdjudicateView.as_view(), name="adjudicate"),
    path("jobs/<uuid:job_id>/", JobStatusView.as_view(), name="job-status"),
    path("jobs/<uuid:job_id>/stream/", job_progress_stream, name="job-progress-stream"),
    path("jobs/<uuid:job_id>/cancel/", CancelJobView.as_view(), name="job-cancel"),
]