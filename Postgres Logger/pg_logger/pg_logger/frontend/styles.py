"""
UI theme and layout constants.
Phase 5: Color palette, card styles, typography.
"""

# Color Palette
COLORS = {
    "primary": "#3B82F6",      # Blue
    "secondary": "#8B5CF6",    # Purple
    "success": "#10B981",      # Green
    "warning": "#F59E0B",      # Orange
    "danger": "#EF4444",       # Red
    "background": "#0F172A",   # Dark blue
    "surface": "#1E293B",      # Slightly lighter
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "border": "#334155",
    
    # Syntax highlighting (Phase 5)
    "syntax_keyword": "#569CD6",     # Blue (SELECT, FROM, WHERE)
    "syntax_function": "#DCDCAA",    # Yellow (COUNT, MAX, AVG)
    "syntax_string": "#CE9178",      # Orange (strings)
    "syntax_number": "#B5CEA8",      # Green (numbers)
}

# Spacing (Reflex-compatible values: '0' through '9')
# These map to Reflex's spacing scale
SPACING = {
    "xs": "1",    # Extra small spacing
    "sm": "2",    # Small spacing
    "md": "4",    # Medium spacing
    "lg": "6",    # Large spacing
    "xl": "8",    # Extra large spacing
}

# Typography
FONTS = {
    "heading": "Inter, system-ui, sans-serif",
    "body": "system-ui, sans-serif",
    "mono": "JetBrains Mono, monospace",
}

# Component styles (to be expanded in Phase 5)
CARD_STYLE = {
    "background": COLORS["surface"],
    "border_radius": "0.5rem",
    "padding": SPACING["md"],
    "border": f"1px solid {COLORS['border']}",
}

BUTTON_STYLE = {
    "primary": {
        "background": COLORS["primary"],
        "color": COLORS["text_primary"],
        "padding": f"{SPACING['sm']} {SPACING['md']}",
        "border_radius": "0.375rem",
        "cursor": "pointer",
    },
    "secondary": {
        "background": COLORS["surface"],
        "color": COLORS["text_primary"],
        "border": f"1px solid {COLORS['border']}",
        "padding": f"{SPACING['sm']} {SPACING['md']}",
        "border_radius": "0.375rem",
        "cursor": "pointer",
    },
}

# SQL Keywords for syntax highlighting (Phase 5)
SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "ON", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS", "NULL",
    "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
    "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
    "CREATE", "TABLE", "ALTER", "DROP", "INDEX",
    "AS", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END",
    "WITH", "UNION", "INTERSECT", "EXCEPT", "ALL", "ANY",
}
