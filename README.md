# Simple Docker Debugger

Two Python classes:
- main.py: DockerDebuggerApp creates FastAPI and registers endpoints with @app.get decorators.
- docker_debugger.py: DockerDebugger contains Docker diagnostic methods.

## Run locally with Python
Install Python and Docker, then run from this folder:

```bash
python -m pip install -r requirements.txt
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Set DEBUGGER_API_TOKEN to the generated value in your shell. On Linux/macOS, use `export DEBUGGER_API_TOKEN='YOUR_GENERATED_TOKEN'`; in PowerShell, use `$env:DEBUGGER_API_TOKEN='YOUR_GENERATED_TOKEN'`.

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8081
```

Open http://localhost:8081/docs, click Authorize, enter the token (without the word Bearer), and use Try it out on an endpoint. Port 8081 avoids conflicting with TWS Labs on port 8080. The Swagger interface needs internet access to load its default assets.

Docker must be running and your Python process must have access to it. The SDK defaults to the local Docker socket. Docker Desktop, rootless Docker or Windows can need additional connection configuration; this app supports Unix sockets and TLS-protected remote TCP hosts, not Windows named pipes. Use WSL with a reachable Unix socket or configure a TLS host.

## Methods
- list_containers: running and stopped containers
- list_images: images and tags
- get_logs: recent stdout/stderr logs
- inspect_container: selected diagnostic fields (excludes environment secrets)
- get_metrics: CPU and memory snapshot for a running container
- close: release the Docker connection

Only diagnostic methods are included. Image build, start/stop, Docker Scout and Trivy scans from the original script are not implemented. This version has no custom dashboard, shared log files or automatic container changes. Returned application logs may still contain sensitive data.

## Docker and Elastic Beanstalk
The ZIP has Dockerfile at its root. Container/service port: 8080. Health check: /healthz. Set DEBUGGER_API_TOKEN before using diagnostic endpoints. Configure HTTPS before entering tokens on a public application endpoint.

The web container needs an explicitly configured Docker connection. Its deployment alone does not provide access to Docker on your computer or on Beanstalk nodes. A healthy /healthz confirms only that the web process runs.

For a remote host, configure DOCKER_HOST=tcp://YOUR_PRIVATE_HOST:2376, DOCKER_TLS_VERIFY=1, DOCKER_CERT_PATH=/run/docker-certs. Supply ca.pem, cert.pem and key.pem securely at runtime. The host needs mutual TLS configured independently and private network access from the web application. No certificates, host or infrastructure are provisioned by this package.

For a local container, mounting a Docker socket requires matching its group permissions to the app's non-root user. Access to that socket grants extensive host control; use a host you own and never give the socket to shared learner terminals. Do not expose an unauthenticated Docker TCP daemon.

## Validation
API tests use a fake Docker connection. Live Docker, container image build and AWS deployment need separate verification. Dependency ranges are not a production lock file.
