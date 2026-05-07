FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONPATH=/workspace/automation-docs/src

COPY automation-docs/src /workspace/automation-docs/src
COPY automation-docs/tests /workspace/automation-docs/tests
COPY config /workspace/config

ENTRYPOINT ["python", "-m", "automation_doc_exporter"]
