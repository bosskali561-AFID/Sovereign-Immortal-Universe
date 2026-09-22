import os
import sys

from app.services.readiness import production_readiness

r = production_readiness()
print(r)

if os.getenv("ENVIRONMENT") == "production" and r["status"] != "READY":
    print("PRODUCTION PREFLIGHT FAILED")
    sys.exit(1)

print("PREFLIGHT PASSED")
