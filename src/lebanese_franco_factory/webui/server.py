"""The combined web app: Dashboard, Datasets, and Review in one server.

Previously the dashboard and review UIs were two separate FastAPI apps on two
ports, yet each rendered the same three-tab nav — so half the tabs 404'd. This
mounts both route sets on a single app so every tab works from one server.
"""

from __future__ import annotations


def create_app():
    """Build the unified FastAPI app (imports fastapi lazily)."""
    from fastapi import FastAPI

    from lebanese_franco_factory.dashboard.app import register_routes as register_dashboard
    from lebanese_franco_factory.review.app import register_routes as register_review

    app = FastAPI(title="Lebanese Franco Factory")
    register_dashboard(app)  # owns "/", "/datasets", "/api/stats", "/generate"
    register_review(app)  # owns "/review" and its sub-routes
    return app


def main(default_port: int = 8090, port_env: str = "LFF_PORT") -> None:
    import os

    import uvicorn

    port = int(os.environ.get(port_env, str(default_port)))
    host = os.environ.get("LFF_HOST", "127.0.0.1")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
