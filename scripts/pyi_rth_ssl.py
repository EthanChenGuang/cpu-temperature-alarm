"""PyInstaller runtime hook — configure certifi CA bundle before any HTTPS imports."""

import os
import sys

if getattr(sys, "frozen", False):
    try:
        import certifi

        bundle = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
    except Exception:
        pass
