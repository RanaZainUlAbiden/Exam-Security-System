"""Single-process WSGI entry point for the complete exam system."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from flask import Flask, jsonify, send_from_directory


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_BUILD = ROOT / "frontend" / "build"


def load_flask_app(module_name, directory):
    app_file = ROOT / directory / "app.py"
    spec = spec_from_file_location(module_name, app_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {app_file}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.app


gateway_app = load_flask_app("exam_logging_gateway", "logging_gateway")
module_apps = {
    number: load_flask_app(f"exam_module_{number:02d}", f"module_{number:02d}")
    for number in range(1, 18)
}

frontend_app = Flask(
    "exam_frontend",
    static_folder=str(FRONTEND_BUILD / "static"),
    static_url_path="/static",
)


@frontend_app.get("/healthz")
def healthz():
    return jsonify({"status": "healthy", "services": 18}), 200


@frontend_app.route("/", defaults={"path": ""})
@frontend_app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"status": "error", "message": "API route not found"}), 404

    requested_file = FRONTEND_BUILD / path
    if path and requested_file.is_file():
        return send_from_directory(FRONTEND_BUILD, path)

    return send_from_directory(FRONTEND_BUILD, "index.html")


class PathDispatcher:
    """Dispatch requests by URL prefix without rewriting PATH_INFO."""

    def __init__(self, fallback, routes):
        self.fallback = fallback
        self.routes = sorted(routes, key=lambda item: len(item[0]), reverse=True)

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        for prefix, app in self.routes:
            if path == prefix or path.startswith(f"{prefix}/"):
                return app(environ, start_response)
        return self.fallback(environ, start_response)


routes = [
    ("/api/logs", gateway_app.wsgi_app),
    ("/api/exam", module_apps[1].wsgi_app),
    ("/dashboard", module_apps[17].wsgi_app),
]
routes.extend(
    (f"/api/module{number:02d}", module_apps[number].wsgi_app)
    for number in range(1, 18)
)

application = PathDispatcher(frontend_app.wsgi_app, routes)
