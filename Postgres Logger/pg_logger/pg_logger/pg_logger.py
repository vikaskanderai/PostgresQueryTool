"""
PostgreSQL Log Streamer - Main application entry point.
"""
import reflex as rx
from .state import AppState
from .frontend.styles import COLORS, SPACING
from .frontend.overlays import restart_warning_overlay
from .frontend.components import control_bar, activity_feed


def index() -> rx.Component:
    """Main page - route based on authentication state."""
    return rx.cond(
        AppState.is_authenticated,
        dashboard_page(),
        rx.cond(
            AppState.requires_restart,
            restart_warning_overlay(AppState.is_polling_restart),
            auth_page()
        )
    )


def auth_page() -> rx.Component:
    """Authentication page with connection form."""
    return rx.box(
        rx.vstack(
            # Header
            rx.heading(
                "PostgreSQL Log Streamer",
                size="9",
                color=COLORS["text_primary"],
                margin_bottom=SPACING["sm"],
            ),
            rx.text(
                "Real-time PostgreSQL query monitoring",
                color=COLORS["text_secondary"],
                margin_bottom=SPACING["xl"],
            ),
            
            # Main content columns
            rx.hstack(
                # Left column: Connection Form
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "Database Connection",
                            size="7",
                            color=COLORS["text_primary"],
                            margin_bottom=SPACING["md"],
                        ),
                        
                        rx.text(
                            "Connect with a superuser account",
                            color=COLORS["text_secondary"],
                            font_size="0.875rem",
                            margin_bottom=SPACING["md"],
                        ),
                        
                        # Host input
                        rx.vstack(
                            rx.text("Host", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="localhost or IP address",
                                value=AppState.selected_host,
                                on_change=AppState.set_selected_host,
                                width="100%",
                                background=COLORS["background"],
                                border=f"1px solid {COLORS['border']}",
                                color=COLORS["text_primary"],
                            ),
                            align_items="start",
                            width="100%",
                            spacing=SPACING["xs"],
                        ),
                        
                        # Port input
                        rx.vstack(
                            rx.text("Port", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="5432",
                                type="number",
                                value=AppState.selected_port,
                                on_change=AppState.set_selected_port,
                                width="100%",
                                background=COLORS["background"],
                                border=f"1px solid {COLORS['border']}",
                                color=COLORS["text_primary"],
                            ),
                            align_items="start",
                            width="100%",
                            spacing=SPACING["xs"],
                        ),
                        
                        # Database input
                        rx.vstack(
                            rx.text("Database", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="postgres",
                                value=AppState.selected_database,
                                on_change=AppState.set_selected_database,
                                width="100%",
                                background=COLORS["background"],
                                border=f"1px solid {COLORS['border']}",
                                color=COLORS["text_primary"],
                            ),
                            align_items="start",
                            width="100%",
                            spacing=SPACING["xs"],
                        ),
                        
                        # Username input
                        rx.vstack(
                            rx.text("Username (Superuser)", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="postgres",
                                value=AppState.selected_username,
                                on_change=AppState.set_selected_username,
                                width="100%",
                                background=COLORS["background"],
                                border=f"1px solid {COLORS['border']}",
                                color=COLORS["text_primary"],
                            ),
                            align_items="start",
                            width="100%",
                            spacing=SPACING["xs"],
                        ),
                        
                        # Password input
                        rx.vstack(
                            rx.text("Password", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="••••••••",
                                type="password",
                                value=AppState.password_input,
                                on_change=AppState.set_password_input,
                                width="100%",
                                background=COLORS["background"],
                                border=f"1px solid {COLORS['border']}",
                                color=COLORS["text_primary"],
                            ),
                            align_items="start",
                            width="100%",
                            spacing=SPACING["xs"],
                        ),
                        
                        # Connect button
                        rx.button(
                            rx.cond(
                                AppState.is_connecting,
                                rx.hstack(
                                    rx.spinner(size="3", color="white"),
                                    rx.text("Connecting..."),
                                    spacing=SPACING["sm"],
                                ),
                                rx.text("Connect to Database"),
                            ),
                            on_click=AppState.connect_to_database(),
                            is_disabled=AppState.is_connecting,
                            width="100%",
                            background=COLORS["primary"],
                            color=COLORS["text_primary"],
                            padding=f"{SPACING['sm']} {SPACING['lg']}",
                            border_radius="0.5rem",
                            cursor="pointer",
                            margin_top=SPACING["md"],
                            _hover={"background": COLORS["secondary"]},
                        ),
                        
                        # Error display
                        rx.cond(
                            AppState.connection_error != "",
                            rx.box(
                                rx.text(
                                    "⚠️ " + AppState.connection_error,
                                    color=COLORS["danger"],
                                    font_size="0.875rem",
                                ),
                                padding=SPACING["md"],
                                background=f"{COLORS['danger']}20",
                                border=f"1px solid {COLORS['danger']}",
                                border_radius="0.5rem",
                                margin_top=SPACING["md"],
                                width="100%",
                            ),
                        ),
                        
                        spacing=SPACING["md"],
                        width="100%",
                    ),
                    padding=SPACING["lg"],
                    background=COLORS["surface"],
                    border_radius="0.75rem",
                    border=f"1px solid {COLORS['border']}",
                    width="100%",
                    max_width="400px",
                ),
                
                # Right column: Discovery & History
                rx.box(
                    rx.vstack(
                        # Network Discovery Section
                        rx.box(
                            rx.heading(
                                "Network Discovery",
                                size="5",
                                color=COLORS["text_primary"],
                                margin_bottom=SPACING["sm"],
                            ),
                            rx.text(
                                "Scan your local network for PostgreSQL instances",
                                color=COLORS["text_secondary"],
                                font_size="0.875rem",
                                margin_bottom=SPACING["md"],
                            ),
                            
                            rx.button(
                                rx.cond(
                                    AppState.is_scanning,
                                    rx.hstack(
                                        rx.spinner(size="3"),
                                        rx.text("Scanning..."),
                                        spacing=SPACING["sm"],
                                    ),
                                    rx.text("Scan Network (5432-5435)"),
                                ),
                                on_click=lambda: AppState.scan_network(),
                                is_disabled=AppState.is_scanning,
                                background=COLORS["secondary"],
                                color=COLORS["text_primary"],
                                width="100%",
                            ),
                            
                            rx.cond(
                                AppState.scan_progress != "",
                                rx.text(
                                    AppState.scan_progress,
                                    color=COLORS["text_secondary"],
                                    font_size="0.875rem",
                                    margin_top=SPACING["sm"],
                                ),
                            ),
                            
                            # Discovered hosts
                            rx.cond(
                                AppState.discovered_hosts.length() > 0,
                                rx.vstack(
                                    rx.foreach(
                                        AppState.discovered_hosts,
                                        lambda host: rx.box(
                                            rx.hstack(
                                                rx.vstack(
                                                    rx.text(
                                                        host["host"],
                                                        color=COLORS["text_primary"],
                                                        font_weight="600",
                                                        font_size="0.875rem",
                                                    ),
                                                    rx.text(
                                                        f"Port {host['port']} • {host['response_time']}ms",
                                                        color=COLORS["text_secondary"],
                                                        font_size="0.75rem",
                                                    ),
                                                    align_items="start",
                                                    spacing="1",
                                                ),
                                                rx.button(
                                                    "Use",
                                                    on_click=AppState.select_host(host["host"], host["port"]),
                                                    size="3",
                                                    background=COLORS["primary"],
                                                    font_size="0.75rem",
                                                ),
                                                justify="between",
                                                width="100%",
                                            ),
                                            padding=SPACING["sm"],
                                            background=COLORS["background"],
                                            border_radius="0.375rem",
                                            margin_top=SPACING["sm"],
                                        ),
                                    ),
                                    width="100%",
                                    max_height="200px",
                                    overflow_y="auto",
                                ),
                            ),
                            
                            width="100%",
                        ),
                        
                        # Connection History
                        rx.box(
                            rx.heading(
                                "Recent Connections",
                                size="5",
                                color=COLORS["text_primary"],
                                margin_bottom=SPACING["sm"],
                            ),
                            
                            rx.cond(
                                AppState.connection_history.length() > 0,
                                rx.vstack(
                                    rx.foreach(
                                        AppState.connection_history[:5],  # Show only 5 most recent
                                        lambda conn, idx: rx.box(
                                            rx.hstack(
                                                rx.vstack(
                                                    rx.text(
                                                        f"{conn['username']}@{conn['host']}",
                                                        color=COLORS["text_primary"],
                                                        font_weight="600",
                                                        font_size="0.875rem",
                                                    ),
                                                    rx.text(
                                                        f"{conn['database']} (port {conn['port']})",
                                                        color=COLORS["text_secondary"],
                                                        font_size="0.75rem",
                                                    ),
                                                    align_items="start",
                                                    spacing="1",
                                                ),
                                                rx.button(
                                                    "Load",
                                                    on_click=AppState.select_from_history(idx),
                                                    size="3",
                                                    background=COLORS["primary"],
                                                    font_size="0.75rem",
                                                ),
                                                justify="between",
                                                width="100%",
                                            ),
                                            padding=SPACING["sm"],
                                            background=COLORS["background"],
                                            border_radius="0.375rem",
                                            margin_top=SPACING["sm"],
                                        ),
                                    ),
                                    width="100%",
                                    max_height="250px",
                                    overflow_y="auto",
                                ),
                                rx.text(
                                    "No previous connections",
                                    color=COLORS["text_secondary"],
                                    font_size="0.875rem",
                                    font_style="italic",
                                ),
                            ),
                            
                            width="100%",
                            margin_top=SPACING["lg"],
                        ),
                        
                        spacing=SPACING["lg"],
                        width="100%",
                    ),
                    padding=SPACING["lg"],
                    background=COLORS["surface"],
                    border_radius="0.75rem",
                    border=f"1px solid {COLORS['border']}",
                    width="100%",
                    max_width="400px",
                ),
                
                spacing=SPACING["lg"],
                align_items="start",
                width="100%",
            ),
            
            width="100%",
            max_width="850px",
            padding=SPACING["xl"],
        ),
        width="100%",
        min_height="100vh",
        background=COLORS["background"],
        display="flex",
        justify_content="center",
        align_items="start",
    )


def dashboard_page() -> rx.Component:
    """Main dashboard with streaming controls."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "PostgreSQL Log Streamer",
                        size="9",
                        color=COLORS["text_primary"],
                    ),
                    rx.text(
                        f"{AppState.selected_username}@{AppState.selected_host}:{AppState.selected_port}/{AppState.selected_database}",
                        color=COLORS["text_secondary"],
                        font_size="0.875rem",
                    ),
                    align_items="start",
                    spacing=SPACING["xs"],
                ),
                rx.button(
                    "Logout",
                    on_click=AppState.reset_connection,
                    background=COLORS["danger"],
                    color=COLORS["text_primary"],
                    padding=f"{SPACING['sm']} {SPACING['md']}",
                    border_radius="0.5rem",
                ),
                justify="between",
                width="100%",
                align_items="center",
            ),
            
            # Control Bar
            control_bar(),
            
            # Activity Feed (Phase 4)
            activity_feed(),
            
            spacing=SPACING["lg"],
            width="100%",
            max_width="1200px",
            padding=SPACING["xl"],
        ),
        width="100%",
        min_height="100vh",
        background=COLORS["background"],
        display="flex",
        justify_content="center",
        align_items="start",
    )


# Create app instance
app = rx.App()
app.add_page(index, on_load=AppState.on_load)
