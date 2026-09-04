import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from infrastructure.persistence.models import Job
job_id = "05d3fab0-a858-4169-9777-2e92fe5e6073"
job = Job.objects.filter(id=job_id).first()
if job:
    print(f"Job Status: {job.status}")
else:
    print("Job not found")
