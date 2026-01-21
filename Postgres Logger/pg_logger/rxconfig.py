"""Reflex configuration for PostgreSQL Log Streamer."""
import reflex as rx

config = rx.Config(
    app_name="pg_logger",
    frontend_port=3000,
    backend_port=8000,
    # Disable sitemap plugin to suppress warnings
    disable_plugins=['reflex.plugins.sitemap.SitemapPlugin'],
)
