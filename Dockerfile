FROM registry.access.redhat.com/ubi8/ubi:8.7-1054

ENV CONFIG_PATH=/ccx-data-pipeline/config.yaml \
    VENV=/ccx-data-pipeline-venv \
    HOME=/ccx-data-pipeline \
    REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt

WORKDIR $HOME

COPY . $HOME

ENV PATH="$VENV/bin:$PATH"

RUN dnf install --nodocs -y python3-pip unzip git-core && \
    python3 -m venv $VENV && \
    curl -ksL https://password.corp.redhat.com/RH-IT-Root-CA.crt \
         -o /etc/pki/ca-trust/source/anchors/RH-IT-Root-CA.crt && \
    update-ca-trust && \
    pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    dnf remove -y git-core && \
    dnf clean all && \
    chmod -R g=u $HOME $VENV /etc/passwd && \
    chgrp -R 0 $HOME $VENV

USER 1001

CMD ["sh", "-c", "ccx-data-pipeline $CONFIG_PATH"]
