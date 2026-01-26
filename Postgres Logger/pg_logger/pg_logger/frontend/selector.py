import reflex as rx
from ..state import AppState

def feature_card(
    title: str, 
    description: str, 
    icon: str, 
    feature_id: str, 
    color: str
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.icon(icon, size=48, color=color),
            rx.heading(title, size="5", color=color),
            rx.text(description, size="2", color="gray"),
            spacing="3",
            align_items="center",
            justify="center",
            text_align="center",
            height="100%",
        ),
        padding="6",
        border=f"1px solid {rx.color(color, 5)}",
        border_radius="xl",
        bg=rx.color(color, 2),
        cursor="pointer",
        _hover={
            "bg": rx.color(color, 3),
            "transform": "scale(1.02)",
            "transition": "all 0.2s",
        },
        on_click=lambda: AppState.select_feature(feature_id),
        width="300px",
        height="200px",
    )

def feature_selector() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Select a Tool", size="7", margin_bottom="6"),
            rx.hstack(
                feature_card(
                    "Query Streamer",
                    "Real-time visibility into database queries and logs.",
                    "activity",
                    "monitor",
                    "blue",
                ),
                feature_card(
                    "Script Generator",
                    "Generate granular deployment scripts for objects.",
                    "file-code",
                    "generator",
                    "green",
                ),
                spacing="6",
            ),
            padding="8",
            align_items="center",
        ),
        height="100%",
    )
