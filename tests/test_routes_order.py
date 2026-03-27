from pathlib import Path
import sys


def test_voices_terms_route_is_search_handler():
    """Ensure the static `/api/voices/terms` route is handled by the
    `voices_search` router (not shadowed by the parameterized CRUD route).

    This catches regressions where include_router order causes `/{voice_id}` to
    greedily match `/terms` and return 404 from the CRUD handler.
    """
    # Ensure src is importable
    sys.path.insert(0, str(Path("src").resolve()))

    from api.app import app

    found = False
    for r in app.routes:
        p = getattr(r, "path", None)
        if p == "/api/voices/terms":
            found = True
            # The endpoint should come from the voices_search module
            ep = getattr(r, "endpoint")
            assert ep.__module__ == "api.routes.voices_search", (
                "Route '/api/voices/terms' is not handled by voices_search; "
                "it may be shadowed by a parameterized route."
            )
            assert "GET" in getattr(r, "methods", set())
    assert found, "Expected route '/api/voices/terms' not found in app.routes"
