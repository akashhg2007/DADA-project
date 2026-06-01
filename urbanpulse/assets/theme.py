# UrbanPulse Design System & Theme Configuration

# 1. Color Palette Dictionary
COLOR_PALETTE = {
    "primary": "#4F46E5",       # Indigo
    "success": "#10B981",       # Emerald Green
    "warning": "#F59E0B",       # Amber Orange
    "danger": "#EF4444",        # Rose Red
    "bg_dark": "#0F172A",        # Slate Dark 900
    "bg_card": "#1E293B",        # Slate Dark 800
    "text_main": "#F1F5F9",      # Slate Light 100
    "text_muted": "#94A3B8"      # Slate Light 400
}

COLORS = COLOR_PALETTE

# 2. Plotly Template Applicator Function
def apply_urbanpulse_theme(fig):
    """Applies global cohesive dark theme aesthetics to any Plotly figure"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, system-ui, -apple-system, sans-serif", 
            color="#F1F5F9",
            size=12
        ),
        legend=dict(
            font=dict(color="#94A3B8"),
            bgcolor="rgba(0,0,0,0)"
        )
    )
    # Apply dark slate grid colors to both axes
    fig.update_xaxes(
        gridcolor="#334155",
        zerolinecolor="#334155",
        tickfont=dict(color="#94A3B8"),
        title=dict(font=dict(color="#F1F5F9"))
    )
    fig.update_yaxes(
        gridcolor="#334155",
        zerolinecolor="#334155",
        tickfont=dict(color="#94A3B8"),
        title=dict(font=dict(color="#F1F5F9"))
    )
    return fig

# 3. Streamlit Page Configuration Dictionary
PAGE_CONFIG = {
    "page_title": "UrbanPulse - Bangalore Traffic & AQI",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# 4. Custom Metric Card HTML Template with Glassmorphism
def get_metric_card_html(title, value, subtitle, badge_html=""):
    """Generates premium glassmorphic HTML card blocks for dashboard KPIs"""
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle" style="display: flex; align-items: center; gap: 0.5rem;">
            {badge_html} <span>{subtitle}</span>
        </div>
    </div>
    """
    return card_html
