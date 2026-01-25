"""
PostgreSQL Log Streamer - Main application entry point.
"""
import reflex as rx
from .state import AppState
from .frontend.styles import COLORS, SPACING, INPUT_STYLE, BUTTON_STYLE
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
    """Authentication page with Side-by-Side Cards."""
def auth_page() -> rx.Component:
    """Authentication page with Side-by-Side Cards."""
    return rx.vstack(
        # Main Header
        rx.heading(
            "Postgres Query Scanner",
            size="9",
            color=COLORS["text_primary"],
            font_weight="700",
            margin_bottom="2rem",
            text_align="center",
        ),
        
        # Content Row
        rx.hstack(
            # LEFT CARD: Connection Form
            rx.box(
                rx.vstack(
                    rx.vstack(
                        rx.heading("Connect to Database", size="6", color=COLORS["text_primary"], font_weight="600"),
                        rx.text("Connect with a superuser account", color=COLORS["text_secondary"], font_size="0.875rem"),
                        spacing="1",
                        width="100%",
                    ),
                    
                    # Host + Port Row
                    rx.hstack(
                        rx.vstack(
                            rx.text("Host", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="localhost",
                                value=AppState.selected_host,
                                on_change=AppState.set_selected_host,
                                **INPUT_STYLE,
                            ),
                            width="70%",
                            spacing=SPACING["xs"],
                            align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Port", color=COLORS["text_secondary"], font_size="0.875rem"),
                            rx.input(
                                placeholder="5432",
                                value=AppState.selected_port,
                                on_change=AppState.set_selected_port,
                                **INPUT_STYLE,
                            ),
                            width="30%",
                            spacing=SPACING["xs"],
                            align_items="start",
                        ),
                        width="100%",
                        spacing=SPACING["md"],
                    ),
                    
                    # Database
                    rx.vstack(
                        rx.text("Database", color=COLORS["text_secondary"], font_size="0.875rem"),
                        rx.input(
                            placeholder="postgres",
                            value=AppState.selected_database,
                            on_change=AppState.set_selected_database,
                            **INPUT_STYLE,
                        ),
                        width="100%",
                        spacing=SPACING["xs"],
                        align_items="start",
                    ),
                    
                    # User
                    rx.vstack(
                        rx.text("Username (Superuser)", color=COLORS["text_secondary"], font_size="0.875rem"),
                        rx.input(
                            placeholder="postgres",
                            value=AppState.selected_username,
                            on_change=AppState.set_selected_username,
                            **INPUT_STYLE,
                        ),
                        width="100%",
                        spacing=SPACING["xs"],
                        align_items="start",
                    ),
                    
                    # Password
                    rx.vstack(
                        rx.text("Password", color=COLORS["text_secondary"], font_size="0.875rem"),
                        rx.input(
                            type="password",
                            placeholder="••••••••",
                            value=AppState.password_input,
                            on_change=AppState.set_password_input,
                            **INPUT_STYLE,
                        ),
                        # Inline Error
                        rx.cond(
                            AppState.connection_error != "",
                            rx.hstack(
                                rx.icon("triangle_alert", size=16, color=COLORS["warning"]),
                                rx.text(
                                    AppState.connection_error,
                                    color=COLORS["warning"],
                                    font_size="0.75rem",
                                ),
                                spacing=SPACING["xs"],
                                margin_top="4px",
                                align_items="center",
                            ),
                        ),
                        width="100%",
                        spacing=SPACING["xs"],
                        align_items="start",
                    ),
                    
                    # Connect Button
                    rx.button(
                        rx.cond(
                            AppState.is_connecting,
                            rx.hstack(
                                rx.spinner(size="2", color="white"),
                                rx.text("Connecting..."),
                                spacing=SPACING["sm"],
                            ),
                            "Connect",
                        ),
                        on_click=AppState.connect_to_database(),
                        is_disabled=AppState.is_connecting,
                        width="100%",
                        margin_top=SPACING["lg"],
                        **BUTTON_STYLE["primary"],
                    ),
                    
                    spacing=SPACING["lg"],
                    width="100%",
                    align_items="start",
                ),
                padding="32px",
                background=COLORS["surface"],
                border=f"1px solid {COLORS['border']}",
                border_radius="1rem",
                width="400px",
            ),
            
            # RIGHT CARD: Environment / Discovery
            rx.box(
                rx.vstack(
                    # Tabs
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Network Scan", value="scan"),
                            rx.tabs.trigger("Recent", value="recent"),
                            background="transparent",
                            border_bottom=f"1px solid {COLORS['border']}",
                            width="100%",
                        ),
                        
                        # NETWORK SCAN TAB
                        rx.tabs.content(
                            rx.vstack(
                                # Discovered List
                                rx.cond(
                                    AppState.discovered_hosts.length() > 0,
                                    rx.vstack(
                                        rx.foreach(
                                            AppState.discovered_hosts,
                                            lambda host: rx.button(
                                                rx.hstack(
                                                    rx.icon("server", size=24, color=COLORS["success"]), # Green icon like image
                                                    rx.vstack(
                                                        rx.text(host["host"], color=COLORS["text_primary"], font_weight="500", font_size="1rem"),
                                                        rx.text(f"Port {host['port']} • {host['response_time']}ms", color=COLORS["text_secondary"], font_size="0.75rem"),
                                                        align_items="start",
                                                        spacing="0",
                                                    ),
                                                    rx.spacer(),
                                                    width="100%",
                                                    align_items="center",
                                                    spacing=SPACING["md"],
                                                ),
                                                on_click=AppState.select_host(host["host"], host["port"]),
                                                padding=SPACING["md"],
                                                background="transparent",
                                                border_radius="0.5rem",
                                                cursor="pointer",
                                                width="100%",
                                                _hover={"background": COLORS["surface_hover"]},
                                                align_items="center",
                                            )
                                        ),
                                        width="100%",
                                        spacing=SPACING["xs"],
                                        margin_top="1.5rem",
                                    ),
                                    rx.vstack(
                                        rx.text("No instances found yet.", color=COLORS["text_secondary"], font_size="0.875rem", margin_top="1.5rem"),
                                        rx.button(
                                            rx.cond(
                                                AppState.is_scanning,
                                                "Scanning...",
                                                "Start Network Scan"
                                            ),
                                            on_click=lambda: AppState.scan_network(),
                                            is_disabled=AppState.is_scanning,
                                            **BUTTON_STYLE["ghost"],
                                            border=f"1px dashed {COLORS['border']}",
                                            width="100%",
                                        ),
                                    ),
                                ),
                                width="100%",
                            ),
                            value="scan",
                            width="100%",
                        ),
                        
                        # RECENT CONNECTIONS TAB
                        rx.tabs.content(
                            rx.vstack(
                                rx.text(
                                    "Recent Connections",
                                    color=COLORS["text_secondary"],
                                    font_size="0.875rem",
                                    margin_top=SPACING["md"],
                                ),
                                
                                rx.cond(
                                    AppState.connection_history.length() > 0,
                                    rx.vstack(
                                        rx.foreach(
                                            AppState.connection_history,
                                            lambda conn, idx: rx.button(
                                                rx.hstack(
                                                    rx.icon("history", size=20, color=COLORS["secondary"]),
                                                    rx.vstack(
                                                        rx.text(f"{conn['username']}@{conn['host']}", color=COLORS["text_primary"], font_weight="500"),
                                                        rx.text(f"{conn['database']} (Port {conn['port']})", color=COLORS["text_secondary"], font_size="0.75rem"),
                                                        align_items="start",
                                                        spacing="0",
                                                    ),
                                                    rx.spacer(),
                                                    rx.icon("arrow-right", color=COLORS["text_secondary"]),
                                                    width="100%",
                                                    align_items="center",
                                                    spacing=SPACING["md"],
                                                ),
                                                on_click=AppState.select_from_history(idx),
                                                padding=SPACING["md"],
                                                background="transparent",
                                                border_radius="0.5rem",
                                                cursor="pointer",
                                                width="100%",
                                                _hover={"background": COLORS["surface_hover"]},
                                            )
                                        ),
                                        width="100%",
                                        spacing=SPACING["xs"],
                                    ),
                                    rx.text("No history available.", color=COLORS["text_secondary"], font_size="0.875rem"),
                                ),
                                width="100%",
                            ),
                            value="recent",
                            width="100%",
                        ),
                        
                        default_value="scan",
                        width="100%",
                    ),
                    width="100%",
                ),
                padding="32px",
                background=COLORS["surface"],
                border=f"1px solid {COLORS['border']}",
                border_radius="1rem",
                width="350px",
                min_height="400px", 
            ),
            
            spacing=SPACING["2xl"],
            align_items="start", 
            flex_wrap="wrap",
            justify_content="center",
        ),
        
        spacing="0",
        width="100%",
        min_height="100vh",
        background=COLORS["background"],
        padding_top="6vh", # Lift content up
        align_items="center",
    )


def dashboard_page() -> rx.Component:
    """Main dashboard with streaming controls."""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "Postgres Query Scanner",
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
                    padding_x=SPACING['md'],
                    padding_y=SPACING['sm'],
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
app = rx.App(stylesheets=["stylesheets.css"])
app.add_page(index, on_load=AppState.on_load)
