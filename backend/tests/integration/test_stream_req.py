import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import RequestFactory

from presentation.api.sse import job_progress_stream

token = os.getenv("JWT_TOKEN")  # Replace with your actual token
job_id = "YOUR_JOB_ID_HERE"  # Replace with the actual job ID
rf = RequestFactory()
request = rf.get(f"/api/jobs/{job_id}/stream/?access={token}")
try:
    response = job_progress_stream(request, job_id)
    if hasattr(response, 'streaming_content'):
        for chunk in response.streaming_content:
            print(chunk)
    else:
        print(response.status_code)
except Exception:
    import traceback
    traceback.print_exc()

