# Streamlit View Routing

Primary deployment entrypoint is `streamlit_app.py` and now supports two explicit views:

- `?view=enduser` (default): investor-facing workspace (`Portfolio`, `Signals`)
- `?view=operator`: ingestion/policy operator dashboard

## Behavior

1. If `view` query param is provided and valid, it is used.
2. If `view` is missing, the app restores the last view stored in Streamlit session state.
3. If `view` is invalid, app falls back to `enduser` and shows a warning.
4. In-app radio toggle keeps both surfaces one-click reachable.

## Access status banner

If `STREAMLIT_PUBLIC_URL` env is configured, both views render the same access health banner using `check_streamlit_access`.
This keeps auth-wall/degraded signals visible regardless of active view.
