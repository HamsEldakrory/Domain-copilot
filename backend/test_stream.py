import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from infrastructure.persistence.models import User, Job, Claim

job_id = "05d3fab0-a858-4169-9777-2e92fe5e6073"
print(f"Testing for job {job_id}")
job = Job.objects.filter(id=job_id).first()
if job:
    print(f"Job found: {job.id}, Claim: {job.claim_id if hasattr(job, 'claim_id') else 'None'}")
    claim = job.claim if hasattr(job, 'claim') else None
    if claim:
        print(f"Claim adjuster: {claim.adjuster_id}")
    else:
        print("Claim is None")
else:
    print("Job not found")

