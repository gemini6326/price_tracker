"""Serve the built panel and the existing API from one cloud process."""

import os
from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from tracker.main import app


class PanelFiles(StaticFiles):
    async def get_response(self, path, scope):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # React routes use index.html; missing assets must remain 404.
            if exc.status_code != 404 or path.startswith("assets/"):
                raise
            return await super().get_response("index.html", scope)


panel = Path(os.environ.get("FRONTEND_DIST", "/app/frontend-dist"))
if not (panel / "index.html").is_file():
    raise RuntimeError("Build the frontend and point FRONTEND_DIST to its dist directory")
app.mount("/", PanelFiles(directory=panel, html=True), name="panel")
