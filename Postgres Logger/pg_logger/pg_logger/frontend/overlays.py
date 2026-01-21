"""
System overlays (restart warning, inactivity pause, etc.).
Full-screen blocking overlays for system-critical states.
"""
import reflex as rx
from .styles import COLORS, SPACING, FONTS


def restart_warning_overlay(is_polling: bool = False) -> rx.Component:
    """
    Full-screen overlay for restart required state.
    Blocks all user interaction until logging_collector is enabled.
    
    Args:
        is_polling: True if actively polling for restart completion
        
    Returns:
        Full-screen modal with restart instructions
    """
    return rx.box(
        rx.vstack(
            # Warning icon
            rx.text(
                "⚠️",
                font_size="4rem",
                margin_bottom=SPACING["md"],
            ),
            
            # Title
            rx.heading(
                "PostgreSQL Restart Required",
                size="9",
                color=COLORS["warning"],
                margin_bottom=SPACING["md"],
            ),
            
            # Message
            rx.vstack(
                rx.text(
                    "The logging_collector setting has been changed to 'on'.",
                    color=COLORS["text_primary"],
                    font_size="1.1rem",
                    text_align="center",
                ),
                rx.text(
                    "PostgreSQL must be restarted for this change to take effect.",
                    color=COLORS["text_secondary"],
                    text_align="center",
                ),
                spacing=SPACING["xs"],
                margin_bottom=SPACING["lg"],
            ),
            
            # Instructions box
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Restart Instructions",
                        size="5",
                        color=COLORS["text_primary"],
                        margin_bottom=SPACING["sm"],
                    ),
                    
                    # Linux
                    rx.vstack(
                        rx.text("Linux:", font_weight="bold", color=COLORS["primary"]),
                        rx.text(
                            "sudo systemctl restart postgresql",
                            font_family=FONTS["mono"],
                            color=COLORS["text_secondary"],
                            padding=SPACING["sm"],
                            background=COLORS["background"],
                            border_radius="0.25rem",
                        ),
                        align_items="start",
                        width="100%",
                    ),
                    
                    # Windows
                    rx.vstack(
                        rx.text("Windows:", font_weight="bold", color=COLORS["primary"]),
                        rx.text(
                            "Restart 'PostgreSQL' service in Services (services.msc)",
                            font_family=FONTS["mono"],
                            color=COLORS["text_secondary"],
                            padding=SPACING["sm"],
                            background=COLORS["background"],
                            border_radius="0.25rem",
                        ),
                        align_items="start",
                        width="100%",
                    ),
                    
                    # Docker
                    rx.vstack(
                        rx.text("Docker:", font_weight="bold", color=COLORS["primary"]),
                        rx.text(
                            "docker restart <container_name>",
                            font_family=FONTS["mono"],
                            color=COLORS["text_secondary"],
                            padding=SPACING["sm"],
                            background=COLORS["background"],
                            border_radius="0.25rem",
                        ),
                        align_items="start",
                        width="100%",
                    ),
                    
                    spacing=SPACING["md"],
                    width="100%",
                ),
                padding=SPACING["lg"],
                background=COLORS["surface"],
                border_radius="0.5rem",
                border=f"1px solid {COLORS['border']}",
                width="100%",
                max_width="600px",
            ),
            
            # Polling indicator
            rx.cond(
                is_polling,
                rx.box(
                    rx.hstack(
                        rx.spinner(
                            color=COLORS["primary"],
                            size="3",
                        ),
                        rx.text(
                            "Checking for restart... (polling every 5 seconds)",
                            color=COLORS["text_secondary"],
                        ),
                        spacing=SPACING["sm"],
                    ),
                    margin_top=SPACING["lg"],
                ),
                rx.box(
                    rx.text(
                        "Waiting for manual restart...",
                        color=COLORS["text_secondary"],
                        font_style="italic",
                    ),
                    margin_top=SPACING["lg"],
                ),
            ),
            
            spacing=SPACING["md"],
            align_items="center",
            max_width="700px",
            padding=SPACING["xl"],
        ),
        # Full-screen overlay styling
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        background="rgba(0, 0, 0, 0.95)",
        z_index="9999",
        display="flex",
        justify_content="center",
        align_items="center",
        backdrop_filter="blur(4px)",
    )


def inactivity_pause_overlay() -> rx.Component:
    """
    Overlay when session is paused due to 10-minute inactivity.
    Phase 6 implementation.
    """
    return rx.box(
        rx.vstack(
            rx.text("⏸️", font_size="3rem"),
            rx.heading("Session Paused", size="9", color=COLORS["warning"]),
            rx.text(
                "Logging disabled due to inactivity to protect disk space.",
                color=COLORS["text_secondary"],
            ),
            rx.button(
                "Resume Session",
                background=COLORS["primary"],
                color=COLORS["text_primary"],
            ),
            spacing=SPACING["lg"],
            align_items="center",
        ),
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        background="rgba(0, 0, 0, 0.9)",
        z_index="9999",
        display="flex",
        justify_content="center",
        align_items="center",
    )


def circuit_breaker_overlay(reason: str = "Unknown") -> rx.Component:
    """
    Emergency overlay when disk usage exceeds thresholds.
    Phase 6 implementation.
    
    Args:
        reason: Reason for circuit breaker activation
    """
    return rx.box(
        rx.vstack(
            rx.text("🚨", font_size="3rem"),
            rx.heading("Emergency Stop", size="9", color=COLORS["danger"]),
            rx.text(
                f"Reason: {reason}",
                color=COLORS["text_primary"],
                font_weight="bold",
            ),
            rx.text(
                "Logging has been automatically disabled for safety.",
                color=COLORS["text_secondary"],
            ),
            spacing=SPACING["lg"],
            align_items="center",
        ),
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        background="rgba(139, 0, 0, 0.9)",  # Dark red
        z_index="9999",
        display="flex",
        justify_content="center",
        align_items="center",
    )
