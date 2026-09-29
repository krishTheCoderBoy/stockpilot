"""Dispatch idempotent seed scripts to the service-owned databases."""
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for service in ("auth-service","inventory-service","procurement-service"):
    service_root=root/"services"/service
    subprocess.run([sys.executable,str(service_root/"scripts"/"seed.py")],cwd=service_root,check=True)
