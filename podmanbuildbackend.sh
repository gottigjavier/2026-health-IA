#!/bin/bash

# Con cambios en nursimg_react
cd health/

# collectstatic del HOST está comentado: usa Python 3.14 del sistema, que no es
# compatible con pyOpenSSL/twisted/daphne (AttributeError: module 'lib' has no
# attribute 'GEN_EMAIL'). Además es redundante: el entrypoint.sh del contenedor
# ya corre collectstatic en runtime con Python 3.12.
cd ..
podman build -t health-app:latest .