from django.urls import path
from presentation.api.sse import job_progress_stream
from presentation.api.views import AdjudicateView, CancelJobView, CreateAdjusterView, CurrentUserView, HealthView, JobStatusView, ReadinessView

urlpatterns = [
    path("adjudicate/", AdjudicateView.as_view(), name="adjudicate"),
    path("jobs/<uuid:job_id>/", JobStatusView.as_view(), name="job-status"),
    path("jobs/<uuid:job_id>/stream/", job_progress_stream, name="job-progress-stream"),
    path("jobs/<uuid:job_id>/cancel/", CancelJobView.as_view(), name="job-cancel"),
    path("users/adjusters/", CreateAdjusterView.as_view(), name="create-adjuster"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("health/", HealthView.as_view()),
    path("health/ready/", ReadinessView.as_view())
]