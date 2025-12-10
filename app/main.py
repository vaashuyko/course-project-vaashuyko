from __future__ import annotations

from typing import Dict, List

from fastapi import FastAPI

from app.core.errors import ApiError, register_exception_handlers
from app.database import Base, engine
from app.routers import auth, wishes

_ITEMS_DB: Dict[str, List[dict]] = {"items": []}


def create_app() -> FastAPI:
    app = FastAPI(
        title="Wishlist API",
        version="1.0.0",
    )

    register_exception_handlers(app)

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/items")
    def create_item(name: str) -> dict:
        if not name or len(name) > 100:
            raise ApiError(
                code="validation_error",
                message="name must be 1..100 chars",
                status_code=422,
            )

        item = {"id": len(_ITEMS_DB["items"]) + 1, "name": name}
        _ITEMS_DB["items"].append(item)
        return item

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        for it in _ITEMS_DB["items"]:
            if it["id"] == item_id:
                return it

        raise ApiError(
            code="not_found",
            message="item not found",
            status_code=404,
        )

    app.include_router(auth.router)
    app.include_router(wishes.router, prefix="/wishes")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
