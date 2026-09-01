from django.urls import path
from presentation.api.views import AdjudicateView, JobStatusView

urlpatterns = [
    path("adjudicate/", AdjudicateView.as_view(), name="adjudicate"),
    path("jobs/<uuid:job_id>/", JobStatusView.as_view(), name="job-status"),
]