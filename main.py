"""Main class registers FastAPI routes using decorators."""
import os
import secrets

from docker.errors import DockerException, NotFound
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from requests.exceptions import RequestException

from docker_debugger import DockerDebugger


class DockerDebuggerApp:
    def __init__(self):
        self.app = FastAPI(title="Simple Docker Debugger")
        self.register_routes()

    def check_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
        expected = os.getenv("DEBUGGER_API_TOKEN", "")
        if len(expected) < 32:
            raise HTTPException(503, "Set DEBUGGER_API_TOKEN to a random token of at least 32 characters.")
        if credentials is None or not secrets.compare_digest(credentials.credentials, expected):
            raise HTTPException(401, "Invalid access token.", headers={"WWW-Authenticate": "Bearer"})

    def get_debugger(self):
        debugger = None
        try:
            debugger = DockerDebugger()
            yield debugger
        except NotFound:
            raise HTTPException(404, "Container not found.")
        except ValueError as error:
            raise HTTPException(400, str(error))
        except (DockerException, RequestException):
            raise HTTPException(502, "Cannot communicate with Docker. Check the connection and permissions.")
        finally:
            if debugger is not None:
                debugger.close()

    def register_routes(self):
        app = self.app
        protected = [Depends(self.check_token)]

        @app.get("/")
        def home():
            return {"message": "Simple Docker Debugger", "api_page": "/docs"}

        @app.get("/healthz")
        def health():
            return {"status": "ok"}

        @app.get("/containers", dependencies=protected)
        def containers(debugger=Depends(self.get_debugger)):
            return debugger.list_containers()

        @app.get("/images", dependencies=protected)
        def images(debugger=Depends(self.get_debugger)):
            return debugger.list_images()

        @app.post("/images/scout", dependencies=protected)
        def scout(image_name: str = Query(..., min_length=1, max_length=255)):
            try:
                return DockerDebugger.scout_scan(image_name)
            except ValueError as error:
                raise HTTPException(400, str(error))
            except BlockingIOError as error:
                raise HTTPException(429, str(error))
            except FileNotFoundError as error:
                raise HTTPException(503, str(error))
            except TimeoutError as error:
                raise HTTPException(504, str(error))
            except OSError:
                raise HTTPException(502, "Docker Scout could not start. Check executable permissions.")

        @app.get("/containers/{name}/logs", dependencies=protected)
        def logs(name: str, tail: int = Query(200, ge=1, le=1000), debugger=Depends(self.get_debugger)):
            return debugger.get_logs(name, tail)

        @app.get("/containers/{name}/inspect", dependencies=protected)
        def inspect(name: str, debugger=Depends(self.get_debugger)):
            return debugger.inspect_container(name)

        @app.get("/containers/{name}/metrics", dependencies=protected)
        def metrics(name: str, debugger=Depends(self.get_debugger)):
            return debugger.get_metrics(name)


application = DockerDebuggerApp()
app = application.app
