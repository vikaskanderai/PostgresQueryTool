import reflex as rx
from ..state import AppState
from .styles import COLORS

def object_checkbox(name: str) -> rx.Component:
    return rx.checkbox(
        name,
        on_change=lambda checked: AppState.toggle_object(name, checked),
        checked=AppState.selected_objects.contains(name),
        color_scheme="green",
    )

def category_list(items: rx.Var[list[str]]) -> rx.Component:
    return rx.vstack(
        rx.foreach(
            items,
            object_checkbox
        ),
        spacing="2",
        align_items="start",
        overflow_y="auto",
        max_height="60vh",
        padding="2",
    )

def object_picker() -> rx.Component:
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Tables", value="tables"),
                rx.tabs.trigger("Views", value="views"),
                rx.tabs.trigger("Functions", value="functions"),
            ),
            rx.tabs.content(
                category_list(AppState.db_objects["tables"]),
                value="tables",
                padding="4",
            ),
            rx.tabs.content(
                category_list(AppState.db_objects["views"]),
                value="views",
                padding="4",
            ),
            rx.tabs.content(
                category_list(AppState.db_objects["functions"]),
                value="functions",
                padding="4",
            ),
            default_value="tables",
        ),
        border="1px solid var(--gray-5)",
        border_radius="md",
        width="100%",
        height="100%",
        background=COLORS["surface"],
        color=COLORS["text_primary"],
    )

def control_panel() -> rx.Component:
    return rx.hstack(
        rx.cond(
            AppState.engine_initialized,
            rx.button(
                "Generate Script", 
                on_click=AppState.run_script_generation,
                loading=AppState.is_generating,
            ),
            rx.button(
                "Initialize Engine", 
                on_click=AppState.initialize_script_engine,
                color_scheme="red",
                variant="outline",
                loading=AppState.is_generating,
            ),
        ),
        rx.spacer(),
        rx.text(
            f"Selected: {AppState.selected_count}", 
            color=COLORS["text_secondary"], 
            size="2"
        ),
        align_items="center",
        width="100%",
        padding_y="2",
    )

def script_preview() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading("Generated Script", size="3", color=COLORS["text_primary"]),
            rx.spacer(),
            rx.button("Copy", size="1", variant="ghost", on_click=rx.set_clipboard(AppState.generated_script)),
            rx.button("Download", size="1", variant="ghost", on_click=rx.download(data=AppState.generated_script, filename="deployment_script.sql")),
            margin_bottom="2",
        ),
        # Container for code block with scroll
        rx.box(
            rx.code_block(
                AppState.generated_script,
                language="sql",
                show_line_numbers=True,
                theme="dracula",
                wrap_long_lines=True,  # This helps with horizontal overflow
            ),
            width="100%",
            height="60vh",
            overflow_y="auto",
            overflow_x="auto",
            background="#282a36",
            border_radius="md",
            padding="4",
        ),
        width="100%",
        padding="4",
        background=COLORS["surface"],
        border_radius="md",
    )

def script_generator_ui() -> rx.Component:
    return rx.grid(
        rx.box(
            rx.heading("Object Selection", size="4", margin_bottom="2", color=COLORS["text_primary"]),
            object_picker(),
            control_panel(),
            padding="4",
            border_right="1px solid var(--gray-4)",
        ),
        rx.box(
            script_preview(),
            padding="4",
        ),
        columns="350px 1fr",
        width="100%",
        height="100%",
    )
