"""
Reusable UI components (cards, buttons, search bars).
Phase 3: Control Bar for streaming controls.
Phase 5: Activity cards, Play/Stop controls, Find module.
"""
import reflex as rx
import re
from ..state import AppState
from .styles import COLORS, SPACING, FONTS, SQL_KEYWORDS


def highlight_sql(sql: str) -> rx.Component:
    """
    Apply syntax highlighting to SQL string.
    Wraps SQL keywords in colored spans.
    
    Args:
        sql: SQL query string
        
    Returns:
        Component with colored keywords
    """
    # Split preserving whitespace
    parts = re.split(r'(\s+)', sql)
    
    components = []
    for part in parts:
        if not part:
            continue
            
        # Check if it's whitespace
        if part.isspace():
            components.append(rx.text(part, as_="span", display="inline"))
            continue
        
        # Check if word (without punctuation) is a keyword
        word_clean = part.strip('(),;').upper()
        
        if word_clean in SQL_KEYWORDS:
            # Highlight keyword
            components.append(
                rx.text(
                    part,
                    as_="span",
                    color=COLORS["syntax_keyword"],
                    font_weight="600",
                    display="inline",
                )
            )
        else:
            # Regular text
            components.append(
                rx.text(
                    part,
                    as_="span",
                    display="inline",
                )
            )
    
    return rx.box(
        *components,
        font_family=FONTS["mono"],
        color=COLORS["text_primary"],
        font_size="0.875rem",
        white_space="pre-wrap",
        word_break="break-word",
    )


def control_bar() -> rx.Component:
    """Control bar with streaming controls and search/filter."""
    return rx.box(
        rx.vstack(
            # Row 1: Play/Stop, Status, Clear
            rx.hstack(
                # Play/Stop Toggle Button
                rx.button(
                    rx.cond(
                        AppState.is_streaming,
                        rx.hstack(
                            rx.text("⏸", font_size="1.2rem"),
                            rx.text("Stop Streaming"),
                            spacing=SPACING["sm"],
                        ),
                        rx.hstack(
                            rx.text("▶️", font_size="1.2rem"),
                            rx.text("Start Streaming"),
                            spacing=SPACING["sm"],
                        ),
                    ),
                    on_click=AppState.toggle_stream(),
                    background=rx.cond(
                        AppState.is_streaming,
                        COLORS["danger"],
                        COLORS["success"]
                    ),
                    color=COLORS["text_primary"],
                    padding_y=SPACING['sm'],
                    padding_x=SPACING['lg'],
                    border_radius="0.5rem",
                    cursor="pointer",
                    font_weight="600",
                    _hover={"opacity": "0.9"},
                ),
                
                # Status Indicator
                rx.hstack(
                    rx.cond(
                        AppState.is_streaming,
                        rx.box(
                            width="10px",
                            height="10px",
                            background=COLORS["success"],
                            border_radius="50%",
                            class_name="pulse-indicator",
                        ),
                        rx.box(
                            width="10px",
                            height="10px",
                            background=COLORS["text_secondary"],
                            border_radius="50%",
                        ),
                    ),
                    rx.text(
                        AppState.stream_status,
                        color=COLORS["text_secondary"],
                        font_size="0.875rem",
                    ),
                    spacing=SPACING["sm"],
                    align_items="center",
                ),
                
                # Clear Feed Button
                rx.button(
                    rx.hstack(
                        rx.text("🗑️", font_size="1rem"),
                        rx.text("Clear Feed"),
                        spacing=SPACING["xs"],
                    ),
                    on_click=AppState.clear_query_log,
                    background=COLORS["surface"],
                    color=COLORS["text_secondary"],
                    border=f"1px solid {COLORS['border']}",
                    padding_y=SPACING['sm'],
                    padding_x=SPACING['md'],
                    border_radius="0.5rem",
                    cursor="pointer",
                    _hover={"background": COLORS["background"]},
                ),
                
                spacing=SPACING["lg"],
                align_items="center",
                justify="between",
                width="100%",
            ),
            
            # Row 2: Search and Filters (Phase 5)
            rx.hstack(
                # Search input
                rx.input(
                    placeholder="🔍 Search SQL, user, or database...",
                    value=AppState.search_text,
                    on_change=AppState.set_search_text,
                    width="400px",
                    background=COLORS["background"],
                    border=f"1px solid {COLORS['border']}",
                    color=COLORS["text_primary"],
                    padding=SPACING["sm"],
                ),
                
                # Duration filter
                rx.input(
                    placeholder="Min duration (ms)",
                    type="number",
                    value=AppState.min_duration,
                    on_change=AppState.set_min_duration,
                    width="150px",
                    background=COLORS["background"],
                    border=f"1px solid {COLORS['border']}",
                    color=COLORS["text_primary"],
                    padding=SPACING["sm"],
                ),
                
                # Result count
                rx.text(
                    f"{AppState.filtered_query_log.length()} / {AppState.query_log.length()} queries",
                    color=COLORS["text_secondary"],
                    font_size="0.875rem",
                ),
                
                spacing=SPACING["md"],
                align_items="center",
                width="100%",
            ),
            
            spacing=SPACING["sm"],
            width="100%",
        ),
        padding=SPACING["md"],
        background=COLORS["surface"],
        border_radius="0.5rem",
        border=f"1px solid {COLORS['border']}",
        margin_bottom=SPACING["lg"],
        width="100%",
    )


def discovery_card(host_data: dict) -> rx.Component:
    """
    Display card for a discovered PostgreSQL instance.
    
    Args:
        host_data: Dictionary with {host, port, status, response_time}
    """
    # TODO: Phase 5 - Full implementation
    return rx.box(
        rx.text(f"{host_data['host']}:{host_data['port']}"),
        padding=SPACING["md"],
        background=COLORS["surface"],
        border_radius="0.5rem",
        margin=SPACING["sm"],
    )


def scan_button() -> rx.Component:
    """Button to trigger network scan."""
    # TODO: Phase 5 - Add loading state and event handler
    return rx.button(
        "Scan Network",
        background=COLORS["primary"],
        color=COLORS["text_primary"],
    )


def connection_form() -> rx.Component:
    """Form for database connection parameters."""
    # TODO: Phase 2 - Full form with host, port, database, username, password
    return rx.fragment()



def query_card(query: dict) -> rx.Component:
    """
    Display card for a single query in the activity feed.
    
    Args:
        query: Dictionary with {timestamp, user, database, sql, duration}
    """
    return rx.box(
        rx.vstack(
            # Header: Timestamp, User, Database, Duration, Copy Button
            rx.hstack(
                rx.hstack(
                    rx.text(
                    query["timestamp"],
                    color=COLORS["text_secondary"],
                    font_size="0.75rem",
                    font_family=FONTS["mono"],
                ),
                rx.text("•", color=COLORS["text_secondary"], font_size="0.75rem"),
                rx.text(
                    f"{query['user']}@{query['database']}",
                    color=COLORS["primary"],
                    font_size="0.75rem",
                    font_weight="600",
                ),
                rx.cond(
                    query.get("duration"),
                    rx.hstack(
                        rx.text("•", color=COLORS["text_secondary"], font_size="0.75rem"),
                        rx.text(
                            f"{query['duration']:.2f}ms",
                            color=COLORS["warning"],
                            font_size="0.75rem",
                            font_weight="600",
                        ),
                        spacing=SPACING["xs"],
                    ),
                ),
                    spacing=SPACING["xs"],
                    align_items="center",
                    flex_wrap="wrap",
                ),
                
                # Copy button
                rx.button(
                    "📋 Copy",
                    on_click=rx.set_clipboard(query["sql"]),
                    size="3",
                    background=COLORS["surface"],
                    border=f"1px solid {COLORS['border']}",
                    color=COLORS["text_secondary"],
                    cursor="pointer",
                    padding_y=SPACING['xs'],
                    padding_x=SPACING['sm'],
                    _hover={"background": COLORS["background"]},
                ),
                
                justify="between",
                width="100%",
                align_items="center",
            ),
            
            # SQL Statement with syntax highlighting
            rx.box(
                rx.code_block(
                    query["sql"],
                    language="sql",
                    show_line_numbers=False,
                    background="transparent",
                    code_tag_props={"style": {"fontFamily": FONTS["mono"], "fontSize": "0.875rem"}},
                ),
                padding=SPACING["sm"],
                background=COLORS["background"],
                border_radius="0.375rem",
                border_left=f"3px solid {COLORS['primary']}",
                margin_top=SPACING["xs"],
                max_width="100%",
                overflow_x="auto",
            ),
            
            align_items="start",
            width="100%",
            spacing=SPACING["xs"],
        ),
        padding=SPACING["md"],
        background=COLORS["surface"],
        border_radius="0.5rem",
        border=f"1px solid {COLORS['border']}",
        margin_bottom=SPACING["sm"],
        width="100%",
        _hover={
            "border_color": COLORS["primary"],
            "box_shadow": "0 2px 8px rgba(0,0,0,0.1)",
        },
    )


def activity_feed() -> rx.Component:
    """Real-time activity feed displaying parsed queries."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Activity Feed",
                    size="7",
                    color=COLORS["text_primary"],
                ),
                rx.text(
                    f"({AppState.filtered_query_log.length()} queries)",
                    color=COLORS["text_secondary"],
                    font_size="0.875rem",
                ),
                spacing=SPACING["sm"],
                align_items="baseline",
            ),
            
            # Feed content
            rx.cond(
                AppState.filtered_query_log.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.filtered_query_log.reverse(),  # Show newest first
                        query_card
                    ),
                    width="100%",
                    spacing=SPACING["sm"],
                ),
                rx.box(
                    rx.cond(
                        AppState.search_text != "",
                        rx.text(
                            "No queries match your search.",
                            color=COLORS["text_secondary"],
                            font_style="italic",
                        ),
                        rx.vstack(
                            rx.text(
                                "No queries captured yet.",
                                color=COLORS["text_secondary"],
                                font_style="italic",
                            ),
                            rx.text(
                                "Start streaming to see real-time query activity.",
                                color=COLORS["text_secondary"],
                                font_size="0.875rem",
                                margin_top=SPACING["xs"],
                            ),
                            align_items="start",
                        ),
                    ),
                    padding=SPACING["lg"],
                ),
            ),
            
            align_items="start",
            width="100%",
            spacing=SPACING["md"],
        ),
        padding=SPACING["lg"],
        background=COLORS["surface_dark"],
        border_radius="0.5rem",
        border=f"1px solid {COLORS['border']}",
        width="100%",
        max_height="600px",
        overflow_y="auto",
    )


def play_stop_toggle() -> rx.Component:
    """Toggle button to enable/disable query streaming."""
    # Deprecated: Use control_bar() instead
    return rx.fragment()


def search_bar() -> rx.Component:
    """Real-time search/filter input for activity feed."""
    # TODO: Phase 5
    return rx.fragment()
