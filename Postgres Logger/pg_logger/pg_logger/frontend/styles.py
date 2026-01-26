"""
UI theme and layout constants.
Phase 5: Color palette, card styles, typography.
"""

# Color Palette
COLORS = {
    # Brand Colors
    "primary": "#3B82F6",        # Blue - Action buttons
    "primary_hover": "#2563EB",  # Blue darken
    "secondary": "#8B5CF6",      # Purple
    "danger": "#EF4444",         # Red
    "success": "#10B981",        # Green
    "warning": "#F59E0B",        # Amber
    "background": "#0F172A",     # Main Background
    
    # Backgrounds (Split View)
    "background_left": "#0F172A",   # Deep Blue/Slate - Auth Panel
    "background_right": "#111827",  # Dark Gray/Black - Discovery Panel
    
    # UI Elements
    "surface": "#1E293B",           # Cards/Input backgrounds
    "surface_dark": "#1F2937",      # Dark Grey - Activity Feed
    "surface_hover": "#334155",     # Hover state for rows
    "surface_hover": "#334155",     # Hover state for rows
    "border": "#334155",            # Borders
    "border_focus": "#3B82F6",      # Input focus border
    "input_bg": "#1E293B",          # Input background
    
    # Text
    "text_primary": "#F8FAFC",      # White/Off-white
    "text_secondary": "#94A3B8",    # Muted slate
    "text_placeholder": "#64748B",  
    
    # Syntax highlighting (Phase 5)
    "syntax_keyword": "#569CD6",     # Blue (SELECT, FROM, WHERE)
    "syntax_function": "#DCDCAA",    # Yellow (COUNT, MAX, AVG)
    "syntax_string": "#CE9178",      # Orange (strings)
    "syntax_number": "#B5CEA8",      # Green (numbers)
}

# Spacing
SPACING = {
    "xs": "2",    # 8px
    "sm": "3",    # 12px
    "md": "4",    # 16px
    "lg": "5",    # 24px
    "xl": "6",    # 32px
    "2xl": "8",   # 48px
}

# Typography
FONTS = {
    "heading": "Inter, system-ui, sans-serif",
    "body": "Inter, system-ui, sans-serif",
    "mono": "JetBrains Mono, monospace",
}

# Component Styles

INPUT_STYLE = {
    "background": COLORS["input_bg"],
    "border": "1px solid transparent",
    "border_radius": "0.5rem",
    "padding": "0 12px", # Reduced vertical padding
    "height": "36px",    # Explicit height
    "color": COLORS["text_primary"],
    "width": "100%",
    "_focus": {
        "border_color": COLORS["border_focus"],
        "box_shadow": f"0 0 0 2px {COLORS['border_focus']}26", # 15% opacity
        "outline": "none",
    },
    "_placeholder": {
        "color": COLORS["text_placeholder"]
    }
}

BUTTON_STYLE = {
    "primary": {
        "background": COLORS["primary"],
        "color": "#FFFFFF",
        "font_weight": "500",
        "height": "36px",
        "padding": "0 16px",
        "border_radius": "0.375rem",
        "transition": "all 0.15s ease",
        "cursor": "pointer",
        "_hover": {
            "background": COLORS["primary_hover"],
            "box_shadow": f"0 0 14px {COLORS['primary']}59", # 35% opacity
        },
        "_disabled": {
            "opacity": 0.7,
            "cursor": "not-allowed",
        }
    },
    "ghost": {
        "background": "transparent",
        "color": COLORS["text_secondary"],
        "cursor": "pointer",
        "_hover": {
            "color": COLORS["text_primary"],
            "background": COLORS["surface_hover"],
        }
    }
}

CARD_STYLE = {
    "background": COLORS["surface"],
    "border_radius": "0.5rem",
    "padding": SPACING["md"],
    "border": f"1px solid {COLORS['border']}",
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
