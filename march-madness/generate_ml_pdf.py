"""
ESPN-styled Machine Learning explainer PDF
Topic: ML explained through March Madness 2026
Audience: Business leaders — keep it simple
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Circle, Polygon, PolyLine
)
from reportlab.graphics import renderPDF
import math

# ── COLOUR PALETTE (ESPN-inspired) ───────────────────────────────────────────
C_NAVY   = colors.HexColor("#001A57")   # ESPN dark navy
C_RED    = colors.HexColor("#D50A0A")   # ESPN red
C_ORANGE = colors.HexColor("#FF4500")   # accent orange
C_GOLD   = colors.HexColor("#FFB612")   # gold / highlight
C_WHITE  = colors.white
C_LGRAY  = colors.HexColor("#F0F2F5")   # light grey background
C_MGRAY  = colors.HexColor("#8A9BB0")   # mid grey text
C_DGRAY  = colors.HexColor("#2C3E50")   # dark text
C_GREEN  = colors.HexColor("#1a8a3f")   # success / positive
C_BLUE   = colors.HexColor("#003399")   # bracket blue

W, H = letter  # 8.5 × 11 in

# ── STYLES ────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "cover_title": ParagraphStyle("cover_title",
            fontName="Helvetica-Bold", fontSize=38, leading=44,
            textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=6),
        "cover_sub": ParagraphStyle("cover_sub",
            fontName="Helvetica", fontSize=14, leading=18,
            textColor=C_GOLD, alignment=TA_CENTER, spaceAfter=12),
        "cover_tag": ParagraphStyle("cover_tag",
            fontName="Helvetica-Bold", fontSize=10, leading=12,
            textColor=C_NAVY, alignment=TA_CENTER),
        "section_label": ParagraphStyle("section_label",
            fontName="Helvetica-Bold", fontSize=9, leading=11,
            textColor=C_ORANGE, spaceAfter=4, spaceBefore=16),
        "section_title": ParagraphStyle("section_title",
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            textColor=C_NAVY, spaceAfter=6),
        "h2": ParagraphStyle("h2",
            fontName="Helvetica-Bold", fontSize=15, leading=19,
            textColor=C_NAVY, spaceAfter=4, spaceBefore=10),
        "h3": ParagraphStyle("h3",
            fontName="Helvetica-Bold", fontSize=12, leading=15,
            textColor=C_NAVY, spaceAfter=3, spaceBefore=8),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=10.5, leading=15,
            textColor=C_DGRAY, spaceAfter=6),
        "body_small": ParagraphStyle("body_small",
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=C_DGRAY, spaceAfter=4),
        "bullet": ParagraphStyle("bullet",
            fontName="Helvetica", fontSize=10.5, leading=15,
            textColor=C_DGRAY, spaceAfter=4, leftIndent=14,
            bulletIndent=0),
        "callout": ParagraphStyle("callout",
            fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=4),
        "stat_big": ParagraphStyle("stat_big",
            fontName="Helvetica-Bold", fontSize=36, leading=40,
            textColor=C_NAVY, alignment=TA_CENTER),
        "stat_label": ParagraphStyle("stat_label",
            fontName="Helvetica", fontSize=9, leading=11,
            textColor=C_MGRAY, alignment=TA_CENTER),
        "caption": ParagraphStyle("caption",
            fontName="Helvetica", fontSize=8.5, leading=11,
            textColor=C_MGRAY, alignment=TA_CENTER, spaceAfter=8),
        "footer": ParagraphStyle("footer",
            fontName="Helvetica", fontSize=8, leading=10,
            textColor=C_MGRAY, alignment=TA_CENTER),
        "tag": ParagraphStyle("tag",
            fontName="Helvetica-Bold", fontSize=8, leading=10,
            textColor=C_WHITE, alignment=TA_CENTER),
        "formula": ParagraphStyle("formula",
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=C_NAVY, alignment=TA_CENTER),
    }


# ── DRAWING HELPERS ───────────────────────────────────────────────────────────

def bar_chart(data, labels, colors_list, width=430, height=120,
              title=None, max_val=None, show_pct=True):
    """Horizontal bar chart."""
    d = Drawing(width, height + (20 if title else 0))
    top_offset = 20 if title else 0
    if title:
        d.add(String(width/2, height + 6, title,
                     fontName="Helvetica-Bold", fontSize=9,
                     fillColor=C_NAVY, textAnchor="middle"))
    n = len(data)
    bar_h = min(20, (height - n * 4) / n)
    if max_val is None:
        max_val = max(data)
    bar_area = width - 110

    for i, (val, lbl, col) in enumerate(zip(data, labels, colors_list)):
        y = height - top_offset - (i + 1) * (bar_h + 4) + 4
        bw = (val / max_val) * bar_area
        d.add(Rect(100, y, bw, bar_h, fillColor=col, strokeColor=None))
        d.add(String(96, y + bar_h/2 - 4, lbl,
                     fontName="Helvetica", fontSize=7.5,
                     fillColor=C_DGRAY, textAnchor="end"))
        label = f"{val*100:.1f}%" if show_pct else str(val)
        d.add(String(102 + bw, y + bar_h/2 - 4, label,
                     fontName="Helvetica-Bold", fontSize=7.5,
                     fillColor=C_DGRAY))
    return d


def flow_diagram(steps, width=470, height=70):
    """Horizontal flow: box → arrow → box → …"""
    d = Drawing(width, height)
    n = len(steps)
    arrow_w = 20
    box_w = (width - arrow_w * (n - 1)) / n
    for i, (label, sub, col) in enumerate(steps):
        x = i * (box_w + arrow_w)
        d.add(Rect(x, 10, box_w, height - 20,
                   fillColor=col, strokeColor=None, rx=3, ry=3))
        d.add(String(x + box_w/2, height - 14, label,
                     fontName="Helvetica-Bold", fontSize=8,
                     fillColor=C_WHITE, textAnchor="middle"))
        if sub:
            d.add(String(x + box_w/2, 18, sub,
                         fontName="Helvetica", fontSize=7,
                         fillColor=colors.HexColor("#CCDDFF"), textAnchor="middle"))
        if i < n - 1:
            ax = x + box_w
            ay = height / 2
            d.add(Line(ax, ay, ax + arrow_w - 4, ay,
                       strokeColor=C_MGRAY, strokeWidth=1.5))
            d.add(Polygon([ax + arrow_w - 4, ay + 4,
                           ax + arrow_w, ay,
                           ax + arrow_w - 4, ay - 4],
                          fillColor=C_MGRAY, strokeColor=None))
    return d


def decision_tree_diagram(width=430, height=200):
    """Simple visual of a decision tree branching."""
    d = Drawing(width, height)
    # Root node
    cx, cy = width/2, height - 30
    r = 22
    d.add(Circle(cx, cy, r, fillColor=C_NAVY, strokeColor=None))
    d.add(String(cx, cy - 4, "Seed\nDiff?",
                 fontName="Helvetica-Bold", fontSize=7,
                 fillColor=C_WHITE, textAnchor="middle"))

    # Level 2
    nodes_l2 = [(cx - 120, height - 95), (cx + 120, height - 95)]
    labels_l2 = ["Win%\nDiff?", "PPG\nDiff?"]
    for (nx, ny), lbl in zip(nodes_l2, labels_l2):
        d.add(Line(cx, cy - r, nx, ny + r,
                   strokeColor=C_MGRAY, strokeWidth=1.2))
        d.add(Circle(nx, ny, r, fillColor=C_BLUE, strokeColor=None))
        d.add(String(nx, ny - 4, lbl,
                     fontName="Helvetica-Bold", fontSize=7,
                     fillColor=C_WHITE, textAnchor="middle"))

    # Level 3 leaves
    leaf_data = [
        (cx - 195, height - 160, "UPSET\nLIKELY", C_ORANGE),
        (cx - 60,  height - 160, "FAVE\nWINS",   C_GREEN),
        (cx + 60,  height - 160, "FAVE\nWINS",   C_GREEN),
        (cx + 195, height - 160, "UPSET\nLIKELY", C_ORANGE),
    ]
    parents = [nodes_l2[0], nodes_l2[0], nodes_l2[1], nodes_l2[1]]
    for (lx, ly, lbl, col), (px, py) in zip(leaf_data, parents):
        d.add(Line(px, py - r, lx, ly + 13,
                   strokeColor=C_MGRAY, strokeWidth=1))
        d.add(Rect(lx - 28, ly, 56, 26, fillColor=col,
                   strokeColor=None, rx=3, ry=3))
        d.add(String(lx, ly + 9, lbl,
                     fontName="Helvetica-Bold", fontSize=6.5,
                     fillColor=C_WHITE, textAnchor="middle"))

    # Legend labels for branches
    d.add(String(cx - 65, height - 68, "Lower",
                 fontName="Helvetica", fontSize=7, fillColor=C_MGRAY))
    d.add(String(cx + 30, height - 68, "Higher",
                 fontName="Helvetica", fontSize=7, fillColor=C_MGRAY))

    # Title
    d.add(String(width/2, 8, "Each branch splits the data — leaves give a win probability",
                 fontName="Helvetica", fontSize=7.5,
                 fillColor=C_MGRAY, textAnchor="middle"))
    return d


def blend_formula_diagram(width=470, height=80):
    """Visual blend formula bar."""
    d = Drawing(width, height)
    total = width - 20
    x0 = 10
    segments = [
        (0.70, "70%  ML Model",        C_NAVY),
        (0.25, "25%  Seed History",     C_BLUE),
        (0.05, "5%   Head-to-Head",     C_ORANGE),
    ]
    x = x0
    y = 30
    h = 28
    for frac, lbl, col in segments:
        w = frac * total
        d.add(Rect(x, y, w, h, fillColor=col, strokeColor=C_WHITE, strokeWidth=1.5))
        d.add(String(x + w/2, y + 10, lbl,
                     fontName="Helvetica-Bold", fontSize=8,
                     fillColor=C_WHITE, textAnchor="middle"))
        x += w
    d.add(String(width/2, 8,
                 "Blended win probability = (0.70 × ML) + (0.25 × Seed History) + (±0.05 × H2H)",
                 fontName="Helvetica-Bold", fontSize=8,
                 fillColor=C_DGRAY, textAnchor="middle"))
    return d


def accuracy_gauge(accuracy=0.6928, width=180, height=110):
    """Semi-circle gauge."""
    d = Drawing(width, height)
    cx, cy = width / 2, 20
    outer_r = 75
    inner_r = 52
    # Background arc segments (grey)
    import math
    steps = 60
    start_deg = 180
    end_deg = 0
    for i in range(steps):
        a1 = math.radians(start_deg - i * 180 / steps)
        a2 = math.radians(start_deg - (i + 1) * 180 / steps)
        frac = i / steps
        if frac < accuracy:
            t = frac / accuracy
            col = colors.linearlyInterpolatedColor(C_ORANGE, C_GREEN, 0, 1, t)
        else:
            col = colors.HexColor("#D8DDE6")
        # Draw thick arc segment as thin rectangle
        mid_a = (a1 + a2) / 2
        mid_r = (outer_r + inner_r) / 2
        px = cx + mid_r * math.cos(mid_a)
        py = cy + mid_r * math.sin(mid_a) + inner_r
        d.add(Rect(px - 3.5, py - 3.5, 7, 7, fillColor=col, strokeColor=None))
    # Center text
    d.add(String(cx, cy + inner_r + 10, f"{accuracy*100:.1f}%",
                 fontName="Helvetica-Bold", fontSize=22,
                 fillColor=C_NAVY, textAnchor="middle"))
    d.add(String(cx, cy + inner_r - 6, "ACCURACY",
                 fontName="Helvetica-Bold", fontSize=7,
                 fillColor=C_MGRAY, textAnchor="middle"))
    d.add(String(cx - outer_r + 5, cy + inner_r + 4, "50%",
                 fontName="Helvetica", fontSize=7,
                 fillColor=C_MGRAY, textAnchor="middle"))
    d.add(String(cx + outer_r - 5, cy + inner_r + 4, "100%",
                 fontName="Helvetica", fontSize=7,
                 fillColor=C_MGRAY, textAnchor="middle"))
    return d


def seed_upset_bars(width=420, height=100):
    """Historical upset rate by seed matchup."""
    d = Drawing(width, height)
    matchups = ["1 vs 16", "2 vs 15", "3 vs 14", "4 vs 13", "5 vs 12", "6 vs 11"]
    upsets =   [0.02,      0.06,       0.15,       0.21,       0.35,       0.37]
    bar_w = (width - 80) / len(matchups) - 6
    bar_area_h = height - 30
    for i, (m, u) in enumerate(zip(matchups, upsets)):
        x = 40 + i * (bar_w + 6)
        bh = u * bar_area_h / 0.4
        col = C_ORANGE if u > 0.3 else (C_GOLD if u > 0.15 else C_BLUE)
        d.add(Rect(x, 20, bar_w, bh, fillColor=col, strokeColor=None, rx=2, ry=2))
        d.add(String(x + bar_w/2, 14, m,
                     fontName="Helvetica", fontSize=7,
                     fillColor=C_DGRAY, textAnchor="middle"))
        d.add(String(x + bar_w/2, 22 + bh, f"{u*100:.0f}%",
                     fontName="Helvetica-Bold", fontSize=7.5,
                     fillColor=C_DGRAY, textAnchor="middle"))
    d.add(String(width/2, height - 8, "Historical upset rate — lower seeds are far safer bets",
                 fontName="Helvetica", fontSize=7.5,
                 fillColor=C_MGRAY, textAnchor="middle"))
    return d


def feature_importance_chart(width=430, height=160):
    features = [
        ("Seed Difference",     0.3642),
        ("Team Seed (A)",       0.1003),
        ("Team Seed (B)",       0.0775),
        ("Point Diff (diff)",   0.0539),
        ("Point Diff (B)",      0.0420),
        ("Point Diff (A)",      0.0399),
        ("Win % (B)",           0.0397),
        ("Points / Game (B)",   0.0380),
    ]
    cols = [C_NAVY, C_BLUE, C_BLUE, C_MGRAY, C_MGRAY, C_MGRAY, C_MGRAY, C_MGRAY]
    return bar_chart(
        [f[1] for f in features],
        [f[0] for f in features],
        cols, width, height,
        title="Feature Importance — What the model cares about most",
        max_val=0.40
    )


def training_loop_diagram(width=430, height=90):
    steps = [
        ("HISTORICAL\nDATA", "5,036 games", C_NAVY),
        ("EXTRACT\nFEATURES", "15 signals", C_BLUE),
        ("TRAIN\nMODEL", "Random Forest", C_BLUE),
        ("PREDICT", "Win Probability", C_ORANGE),
        ("EVALUATE", "69.3% Accurate", C_GREEN),
    ]
    return flow_diagram(steps, width, height)


def business_use_case_diagram(width=430, height=80):
    steps = [
        ("RAW\nDATA", "Sales / ops / HR", C_NAVY),
        ("EXTRACT\nFEATURES", "Key metrics", C_BLUE),
        ("ML\nMODEL", "Pattern learned", C_BLUE),
        ("SCORE", "Probability", C_ORANGE),
        ("ACTION", "Decision made", C_GREEN),
    ]
    return flow_diagram(steps, width, height)


# ── CANVAS DECORATIONS ────────────────────────────────────────────────────────

def draw_header_band(c, y, label, text, height=40):
    c.setFillColor(C_NAVY)
    c.rect(0, y, W, height, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, y + height - 14, label)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y + 10, text)


def draw_stat_box(c, x, y, w, h, big, label, bg=C_NAVY):
    c.setFillColor(bg)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=0)
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(x + w/2, y + h/2 + 2, big)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + w/2, y + 10, label)


def draw_tag(c, x, y, text, bg=C_ORANGE, fg=C_WHITE):
    tw = c.stringWidth(text, "Helvetica-Bold", 8) + 12
    c.setFillColor(bg)
    c.roundRect(x, y, tw, 16, 3, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 6, y + 4, text)


def draw_quote_box(c, x, y, w, h, text, sub=None):
    c.setFillColor(C_LGRAY)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.rect(x, y, 4, h, fill=1, stroke=0)
    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica-BoldOblique", 11)
    # Wrap text manually
    lines = text.split("\n")
    ty = y + h - 18
    for line in lines:
        c.drawString(x + 14, ty, line)
        ty -= 14
    if sub:
        c.setFont("Helvetica", 8.5)
        c.setFillColor(C_MGRAY)
        c.drawString(x + 14, y + 8, sub)


def draw_page_footer(c, page_num, total=8):
    c.setFillColor(C_NAVY)
    c.rect(0, 0, W, 28, fill=1, stroke=0)
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, 9, "DEAD RECKONING  ·  MARCH MADNESS 2026  ·  MACHINE LEARNING EXPLAINER")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - 40, 9, f"PAGE {page_num} OF {total}")


def draw_section_divider(c, y, text):
    c.setFillColor(C_ORANGE)
    c.rect(40, y, 3, 20, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y + 4, text)


# ── PAGE BUILDERS ─────────────────────────────────────────────────────────────

def build_cover(c):
    # Full navy background
    c.setFillColor(C_NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Diagonal grid lines (ESPN feel)
    c.setStrokeColor(colors.HexColor("#0A2878"))
    c.setLineWidth(0.5)
    for i in range(-10, 25):
        c.line(i * 40, 0, i * 40 + H, H)

    # Top red bar
    c.setFillColor(C_RED)
    c.rect(0, H - 10, W, 10, fill=1, stroke=0)

    # Gold accent stripe
    c.setFillColor(C_GOLD)
    c.rect(0, H - 16, W, 6, fill=1, stroke=0)

    # ESPN-style top label
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W/2, H - 40, "NCAA MARCH MADNESS 2026  ·  BUSINESS INTELLIGENCE SERIES")

    # Main title
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 44)
    c.drawCentredString(W/2, H - 100, "MACHINE")
    c.drawCentredString(W/2, H - 150, "LEARNING")

    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 44)
    c.drawCentredString(W/2, H - 200, "EXPLAINED")

    # Subtitle
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica", 15)
    c.drawCentredString(W/2, H - 240,
        "How a basketball bracket prediction model")
    c.drawCentredString(W/2, H - 258,
        "reveals exactly how AI works — in plain English")

    # Bracket bracket visual (decorative)
    bracket_top = H - 300
    c.setFillColor(colors.HexColor("#0A2878"))
    c.rect(40, bracket_top - 200, W - 80, 200, fill=1, stroke=0)

    # Mock bracket lines
    c.setStrokeColor(colors.HexColor("#1A3A8F"))
    c.setLineWidth(1)
    col_x = [80, 170, 260, 355, 450]
    for x in col_x:
        c.line(x, bracket_top - 200, x, bracket_top - 10)

    # Team slots
    team_data = [
        (80, ["1 DUKE", "16 ALBANY", "8 MEMPHIS", "9 VANDERBILT"]),
        (170, ["DUKE", "MEMPHIS"]),
        (260, ["DUKE"]),
        (355, ["DUKE", "AUBURN"]),
        (450, ["AUBURN", "KENTUCKY"]),
    ]
    c.setFont("Helvetica-Bold", 6)
    for col_x2, teams in team_data:
        spacing = 190 / (len(teams) + 1)
        for i, team in enumerate(teams):
            ty = bracket_top - 190 + i * spacing + spacing
            c.setFillColor(colors.HexColor("#1A3A8F"))
            c.rect(col_x2, ty - 6, 75, 13, fill=1, stroke=0)
            c.setFillColor(C_WHITE if "DUKE" in team else C_GOLD)
            c.drawString(col_x2 + 4, ty - 2, team)

    # Champion tag
    c.setFillColor(C_GOLD)
    c.roundRect(W/2 - 70, bracket_top - 155, 140, 24, 4, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W/2, bracket_top - 147, "CHAMPION: DUKE  (71.4%)")

    # Stats row
    stats = [
        ("69.3%", "MODEL ACCURACY"),
        ("5,036", "GAMES TRAINED ON"),
        ("25+", "YEARS OF DATA"),
        ("15", "INPUT FEATURES"),
    ]
    sx = 40
    sw = (W - 80) / 4
    sy = 120
    for big, lbl in stats:
        c.setFillColor(colors.HexColor("#0A2878"))
        c.roundRect(sx + 4, sy, sw - 8, 60, 4, fill=1, stroke=0)
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(sx + sw/2, sy + 32, big)
        c.setFillColor(C_MGRAY)
        c.setFont("Helvetica", 7)
        c.drawCentredString(sx + sw/2, sy + 16, lbl)
        sx += sw

    # Bottom bar
    c.setFillColor(C_ORANGE)
    c.rect(0, 28, W, 6, fill=1, stroke=0)
    draw_page_footer(c, 1)
    c.showPage()


def build_page2(c, S):
    """What IS Machine Learning?"""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Header band
    c.setFillColor(C_NAVY)
    c.rect(0, H - 55, W, 55, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 18, "SECTION 01  ·  THE BIG IDEA")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 46, "WHAT IS MACHINE LEARNING?")
    draw_page_footer(c, 2)

    y = H - 80

    # Big analogy block
    c.setFillColor(C_LGRAY)
    c.roundRect(40, y - 110, W - 80, 100, 6, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.roundRect(40, y - 110, W - 80, 100, 6, fill=0, stroke=1)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(54, y - 22, "THE ANALOGY")
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-BoldOblique", 13)
    c.drawString(54, y - 40, '"Think of a veteran scout who has watched 5,000 basketball games.')
    c.drawString(54, y - 56, " Over time, they just know: when a #1 seed plays a #16 seed,")
    c.drawString(54, y - 72, " the #1 almost always wins. Machine learning is that scout")
    c.drawString(54, y - 88, ' — except it never sleeps, and it never forgets."')
    c.setFillColor(C_MGRAY)
    c.setFont("Helvetica", 8)
    c.drawString(54, y - 104, "Dead Reckoning  ·  March Madness 2026 ML Explainer")

    y -= 130

    # Three-column explanation
    col_w = (W - 100) / 3
    col_data = [
        (C_NAVY,   "TRADITIONAL\nSOFTWARE",
         "You write the rules.\nIF seed < 5 THEN\npredict win.\n\nWorks for simple\nproblems. Breaks\ndown with complexity.",
         "Rules → Output"),
        (C_BLUE,   "MACHINE\nLEARNING",
         "The algorithm\nfinds the rules.\nYou show it examples\n(past games) and it\ndiscovers the patterns\nby itself.",
         "Data → Rules → Output"),
        (C_GREEN,  "THE RESULT",
         "A model that can\npredict a Duke vs\nConnecticut winner\nbased on 15 hidden\nsignals — no human\nexpert needed.",
         "69.3% Accuracy"),
    ]
    cx = 40
    for bg, title, body, tag_txt in col_data:
        c.setFillColor(bg)
        c.roundRect(cx, y - 155, col_w - 8, 145, 5, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 10)
        for ti, tline in enumerate(title.split("\n")):
            c.drawCentredString(cx + (col_w-8)/2, y - 20 - ti*12, tline)
        c.setFillColor(colors.HexColor("#B0C4DE") if bg == C_NAVY else colors.HexColor("#E8F5E9"))
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 8.5)
        ty = y - 48
        for line in body.split("\n"):
            c.drawString(cx + 8, ty, line)
            ty -= 12
        # tag
        draw_tag(c, cx + 8, y - 148, tag_txt, C_GOLD, C_NAVY)
        cx += col_w + 4

    y -= 180

    draw_section_divider(c, y + 10, "WHY DOES THIS MATTER FOR BUSINESS?")
    y -= 20

    business = [
        ("Sales Forecasting", "Which deals will close? Same math as 'which team will win?'"),
        ("Churn Prediction",  "Which customers will leave? Feed in usage data, model flags risk."),
        ("Fraud Detection",   "Which transaction is fake? Model learns from 10,000 past frauds."),
        ("Hiring",            "Which candidate succeeds? Model finds hidden patterns in resumes."),
    ]
    bx = 40
    bw = (W - 100) / 2
    by = y
    for i, (title, desc) in enumerate(business):
        col = i % 2
        row = i // 2
        bxc = bx + col * (bw + 10)
        byc = by - row * 50
        c.setFillColor(C_LGRAY)
        c.roundRect(bxc, byc - 38, bw, 42, 4, fill=1, stroke=0)
        c.setFillColor(C_ORANGE)
        c.roundRect(bxc, byc - 38, 4, 42, 0, fill=1, stroke=0)
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(bxc + 12, byc - 12, title)
        c.setFillColor(C_DGRAY)
        c.setFont("Helvetica", 8.5)
        c.drawString(bxc + 12, byc - 26, desc)

    c.showPage()


def build_page3(c, S):
    """The Data — Inputs to the Model"""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(C_NAVY)
    c.rect(0, H - 55, W, 55, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 18, "SECTION 02  ·  THE RAW MATERIAL")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 46, "THE DATA: WHAT GOES INTO THE MODEL?")
    draw_page_footer(c, 3)

    y = H - 75

    # Intro
    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica", 11)
    c.drawString(40, y, "Every ML model starts with data. Garbage in = garbage out. Here is exactly what our model ate.")
    y -= 25

    # Two-column: sources
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "WHERE THE DATA COMES FROM")
    y -= 14

    sources = [
        ("ESPN / NCAA",   "Game-by-game results 2000–2025", "Public"),
        ("Kaggle",        "Pre-cleaned historical tournament data", "Public"),
        ("KenPom-style",  "Efficiency ratings, tempo, strength of schedule", "Derived"),
        ("2026 Season",   "Current season stats scraped pre-tournament", "Live"),
    ]
    c.setFillColor(C_LGRAY)
    c.rect(40, y - len(sources)*20 - 10, W - 80, len(sources)*20 + 18, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(48, y - 4, "SOURCE")
    c.drawString(170, y - 4, "DESCRIPTION")
    c.drawString(390, y - 4, "TYPE")
    c.line(40, y - 8, W - 40, y - 8)
    c.setLineWidth(0.5); c.setStrokeColor(C_MGRAY)
    c.line(40, y - 8, W - 40, y - 8)
    ty = y - 20
    for src, desc, typ in sources:
        c.setFillColor(C_DGRAY); c.setFont("Helvetica-Bold", 9)
        c.drawString(48, ty, src)
        c.setFont("Helvetica", 9)
        c.drawString(170, ty, desc)
        c.setFont("Helvetica-Bold", 8)
        tag_col = C_GREEN if typ == "Public" else (C_BLUE if typ == "Derived" else C_ORANGE)
        draw_tag(c, 390, ty - 4, typ, tag_col)
        ty -= 20

    y = ty - 15

    # Feature table
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "THE 15 FEATURES (INPUTS) THE MODEL USES")
    y -= 10

    features = [
        ("seed_diff",        "Seed A − Seed B",           "36.4%", "HIGHEST"),
        ("seed_a",           "Seed of Team A",             "10.0%", "HIGH"),
        ("seed_b",           "Seed of Team B",             " 7.8%", "HIGH"),
        ("point_diff_diff",  "Avg margin A − margin B",    " 5.4%", "MED"),
        ("point_diff_a/b",   "Avg scoring margin each team"," 8.2%","MED"),
        ("win_pct_a/b",      "Season win percentage",      " 7.6%", "MED"),
        ("ppg_a/b",          "Points per game",            " 7.5%", "MED"),
        ("opp_ppg_a/b",      "Opponent points allowed",    " 6.7%", "MED"),
        ("win_pct_diff",     "Win % A − Win % B",          " 3.6%", "LOW"),
        ("ppg_diff",         "PPG A − PPG B",              " 3.5%", "LOW"),
        ("opp_ppg_diff",     "Opp PPG A − Opp PPG B",     " 3.4%", "LOW"),
    ]

    # Header
    c.setFillColor(C_NAVY)
    c.rect(40, y - 14, W - 80, 14, fill=1, stroke=0)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(48, y - 10, "FEATURE NAME")
    c.drawString(188, y - 10, "WHAT IT MEASURES")
    c.drawString(368, y - 10, "IMPORTANCE")
    c.drawString(430, y - 10, "SIGNAL STRENGTH")
    y -= 14

    for i, (feat, desc, imp, strength) in enumerate(features):
        bg = C_WHITE if i % 2 == 0 else C_LGRAY
        c.setFillColor(bg)
        c.rect(40, y - 13, W - 80, 13, fill=1, stroke=0)
        c.setFillColor(C_DGRAY)
        c.setFont("Courier-Bold" if i < 3 else "Courier", 8)
        c.drawString(48, y - 10, feat)
        c.setFont("Helvetica", 8.5)
        c.drawString(188, y - 10, desc)
        c.setFont("Helvetica-Bold", 8)
        imp_col = C_RED if strength == "HIGHEST" else (C_ORANGE if strength == "HIGH" else (C_BLUE if strength == "MED" else C_MGRAY))
        c.setFillColor(imp_col)
        c.drawString(368, y - 10, imp)
        draw_tag(c, 430, y - 12, strength,
                 C_RED if strength == "HIGHEST" else (C_ORANGE if strength == "HIGH" else (C_BLUE if strength == "MED" else C_MGRAY)))
        y -= 13

    y -= 16
    # Feature importance chart
    d = feature_importance_chart(430, 140)
    renderPDF.draw(d, c, 40, y - 140)
    y -= 155

    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica", 9)
    c.drawString(40, y, "KEY INSIGHT: Seed difference alone accounts for 36% of the model's decision. The committee's seeding process is surprisingly predictive.")

    c.showPage()


def build_page4(c, S):
    """How The Model Learns"""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(C_NAVY)
    c.rect(0, H - 55, W, 55, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 18, "SECTION 03  ·  THE ENGINE")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 46, "HOW THE MODEL LEARNS")
    draw_page_footer(c, 4)

    y = H - 72

    # Training pipeline
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "THE TRAINING PIPELINE")
    y -= 6

    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Before the model can predict anything, it has to study. Here is how:")
    y -= 18

    d = training_loop_diagram(W - 80, 80)
    renderPDF.draw(d, c, 40, y - 80)
    y -= 100

    # Step-by-step callout boxes
    steps = [
        ("01", "GATHER HISTORICAL DATA",
         "We collected 5,036 tournament games going back to 2000. Each row in our dataset\n"
         "is one game: Duke vs Connecticut, their stats, and who actually won."),
        ("02", "EXTRACT 15 FEATURES",
         "For every game we calculate 15 numbers (seed, win %, points scored, etc.).\n"
         "These become the model's 'senses' — the only things it can look at."),
        ("03", "TRAIN A RANDOM FOREST",
         "We grow 500 decision trees. Each tree learns slightly different rules from a\n"
         "random slice of the data. Together, they vote on the winner."),
        ("04", "TEST & EVALUATE",
         "We hide 20% of games from training and test the model on those. It gets\n"
         "69.3% correct — well above the 50% random baseline."),
    ]
    for step_num, title, body in steps:
        c.setFillColor(C_LGRAY)
        c.roundRect(40, y - 62, W - 80, 56, 4, fill=1, stroke=0)
        # Number badge
        c.setFillColor(C_NAVY)
        c.circle(62, y - 34, 16, fill=1, stroke=0)
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(62, y - 38, step_num)
        # Title
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(86, y - 20, title)
        # Body
        c.setFillColor(C_DGRAY)
        c.setFont("Helvetica", 9)
        for line in body.split("\n"):
            c.drawString(86, y - 34, line)
            y -= 12
        y -= 30

    y -= 10

    # Decision tree visual
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "WHAT A DECISION TREE LOOKS LIKE (SIMPLIFIED)")
    y -= 8

    d = decision_tree_diagram(W - 80, 180)
    renderPDF.draw(d, c, 40, y - 180)
    y -= 195

    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica", 9)
    c.drawString(40, y, "The Random Forest model runs 500 of these trees and takes a majority vote for each matchup.")

    c.showPage()


def build_page5(c, S):
    """Three Prediction Signals"""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(C_NAVY)
    c.rect(0, H - 55, W, 55, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 18, "SECTION 04  ·  THE THREE SIGNALS")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 46, "HOW WE BLEND THREE PREDICTION SIGNALS")
    draw_page_footer(c, 5)

    y = H - 74

    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica", 10.5)
    c.drawString(40, y, "No single algorithm is perfect. We combine three signals, each with a specific job.")
    y -= 20

    # Three signal cards
    card_w = (W - 100) / 3
    card_data = [
        (C_NAVY,   "SIGNAL 1",   "ML MODEL",
         "Random Forest trained\non 5,036 historical games.\n\nLooks at all 15 features\nsimultaneously and\nfinds patterns no human\nwould ever spot.",
         "70%", "WEIGHT"),
        (C_BLUE,   "SIGNAL 2",   "SEED HISTORY",
         "Pure historical upset\nrates by seed matchup.\n\n1 vs 16: only 2% upset.\n5 vs 12: 35% upset.\n\nAnchors the model\nin tournament reality.",
         "25%", "WEIGHT"),
        (C_ORANGE, "SIGNAL 3",   "HEAD-TO-HEAD",
         "Did these two teams\nplay during the season?\nIf so, apply a small\nadjustment based on\nthat result.\n\nHuman intuition baked in.",
         "±5%", "ADJUST"),
    ]
    cx = 40
    for bg, label, title, body, pct, pct_lbl in card_data:
        c.setFillColor(bg)
        c.roundRect(cx, y - 215, card_w - 8, 205, 5, fill=1, stroke=0)
        # Label
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(cx + 10, y - 18, label)
        # Title
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(cx + 10, y - 34, title)
        # Divider
        c.setFillColor(colors.HexColor("#FFFFFF40") if bg != C_ORANGE else colors.HexColor("#00000020"))
        c.rect(cx + 10, y - 40, card_w - 28, 1, fill=1, stroke=0)
        # Body
        c.setFillColor(C_WHITE if bg != C_ORANGE else C_WHITE)
        c.setFont("Helvetica", 8.5)
        ty = y - 58
        for line in body.split("\n"):
            c.drawString(cx + 10, ty, line)
            ty -= 12
        # Weight badge
        c.setFillColor(C_GOLD)
        c.roundRect(cx + 10, y - 208, card_w - 28, 36, 4, fill=1, stroke=0)
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(cx + (card_w-8)/2, y - 192, pct)
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx + (card_w-8)/2, y - 205, pct_lbl)
        cx += card_w + 4

    y -= 228

    # Blend formula visual
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "THE BLEND FORMULA")
    y -= 8

    d = blend_formula_diagram(W - 80, 80)
    renderPDF.draw(d, c, 40, y - 80)
    y -= 95

    # Historical upset chart
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "WHY SEED HISTORY MATTERS: HISTORICAL UPSET RATES")
    y -= 8

    d = seed_upset_bars(W - 80, 105)
    renderPDF.draw(d, c, 40, y - 105)
    y -= 120

    draw_quote_box(c, 40, y - 50, W - 80, 44,
        '"The lower the seed difference, the more the ML model matters.',
        "The higher the seed difference, the more history matters. That's the art of the blend.")

    c.showPage()


def build_page6(c, S):
    """The Results"""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(C_NAVY)
    c.rect(0, H - 55, W, 55, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 18, "SECTION 05  ·  THE RESULTS")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 46, "THE 2026 PREDICTIONS")
    draw_page_footer(c, 6)

    y = H - 72

    # Gauge + stats row
    gauge = accuracy_gauge(0.6928, 180, 110)
    renderPDF.draw(gauge, c, 40, y - 115)

    # Stats alongside gauge
    stats = [
        ("5,036", "GAMES IN TRAINING DATA"),
        ("25+",   "YEARS OF HISTORY"),
        ("15",    "INPUT FEATURES"),
        ("500",   "DECISION TREES IN THE FOREST"),
    ]
    sx = 230
    sw = 80
    sy = y - 55
    for big, lbl in stats:
        c.setFillColor(C_LGRAY)
        c.roundRect(sx, sy - 36, sw, 36, 4, fill=1, stroke=0)
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(sx + sw/2, sy - 14, big)
        c.setFillColor(C_MGRAY)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(sx + sw/2, sy - 28, lbl)
        sx += sw + 8

    y -= 130

    # Championship bracket box
    c.setFillColor(C_NAVY)
    c.roundRect(40, y - 145, W - 80, 135, 6, fill=1, stroke=0)

    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y - 18, "2026 PREDICTED CHAMPIONSHIP MATCHUP")
    c.setFillColor(C_MGRAY)
    c.setFont("Helvetica", 8)
    c.drawString(55, y - 30, "Mon April 6 · 8:30PM ET · AT&T Stadium · San Antonio")

    # Left finalist
    lf_x, lf_y, lf_w, lf_h = 55, y - 115, 185, 68
    c.setFillColor(colors.HexColor("#1A3A8F"))
    c.roundRect(lf_x, lf_y, lf_w, lf_h, 4, fill=1, stroke=0)
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(lf_x + 8, lf_y + lf_h - 16, "FINALIST · EAST REGION")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(lf_x + 8, lf_y + 28, "DUKE")
    c.setFont("Helvetica", 9)
    c.drawString(lf_x + 8, lf_y + 14, "#1 Seed · 71.4% to win title")

    # VS
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString((55 + 185 + W - 40 - 185) / 2, y - 84, "VS")

    # Right finalist
    rf_x = W - 40 - 185
    c.setFillColor(colors.HexColor("#1A3A8F"))
    c.roundRect(rf_x, lf_y, lf_w, lf_h, 4, fill=1, stroke=0)
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(rf_x + 8, lf_y + lf_h - 16, "FINALIST · WEST REGION")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(rf_x + 8, lf_y + 28, "AUBURN")
    c.setFont("Helvetica", 9)
    c.drawString(rf_x + 8, lf_y + 14, "#1 Seed · 28.6% to win title")

    # Champion ribbon
    c.setFillColor(C_GOLD)
    c.roundRect(W/2 - 80, y - 138, 160, 22, 4, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W/2, y - 130, "PREDICTED CHAMPION:  #1 DUKE")

    y -= 165

    # Region champions table
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "PREDICTED FINAL FOUR")
    y -= 8

    regions = [
        ("EAST",    "#1 DUKE",         "71.4% champ prob",  C_RED),
        ("WEST",    "#1 AUBURN",        "28.6% champ prob",  C_BLUE),
        ("MIDWEST", "#1 HOUSTON",       "Conference fave",   C_ORANGE),
        ("SOUTH",   "#1 FLORIDA",       "Strong ML signal",  C_GREEN),
    ]
    rw = (W - 100) / 4
    rx = 40
    for region, team, note, col in regions:
        c.setFillColor(C_LGRAY)
        c.roundRect(rx, y - 62, rw - 6, 56, 4, fill=1, stroke=0)
        c.setStrokeColor(col)
        c.setLineWidth(2)
        c.roundRect(rx, y - 62, rw - 6, 56, 4, fill=0, stroke=1)
        c.setLineWidth(1)
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(rx + 8, y - 16, region)
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(rx + 8, y - 32, team)
        c.setFillColor(C_MGRAY)
        c.setFont("Helvetica", 8)
        c.drawString(rx + 8, y - 46, note)
        rx += rw + 2

    y -= 80

    # Tiebreaker box
    c.setFillColor(C_LGRAY)
    c.roundRect(40, y - 50, W - 80, 44, 4, fill=1, stroke=0)
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y - 16, "TIEBREAKER PREDICTION: TOTAL COMBINED FINAL SCORE")
    c.setFillColor(C_DGRAY)
    c.setFont("Helvetica", 9.5)
    c.drawString(55, y - 30,
        "Model predicts: 115 combined points   |   Duke 62  —  Auburn 53")
    c.setFillColor(C_MGRAY)
    c.setFont("Helvetica", 8)
    c.drawString(55, y - 44, "Used for bracket tiebreakers. Based on average scoring in similar matchups.")

    c.showPage()


def build_page7(c, S):
    """What This Means for Business"""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(C_NAVY)
    c.rect(0, H - 55, W, 55, fill=1, stroke=0)
    c.setFillColor(C_ORANGE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 18, "SECTION 06  ·  YOUR PLAYBOOK")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 46, "WHAT THIS MEANS FOR YOUR BUSINESS")
    draw_page_footer(c, 7)

    y = H - 72

    # Mapping
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "MARCH MADNESS → BUSINESS: THE DIRECT MAPPING")
    y -= 12

    mappings = [
        ("MARCH MADNESS",       "YOUR BUSINESS"),
        ("Team stats (PPG, W%)", "Customer data (spend, tenure, usage)"),
        ("Tournament result",    "Business outcome (churn, purchase, fraud)"),
        ("Seed (ranking)",       "Customer tier or account size"),
        ("Historical games",     "Your historical transaction records"),
        ("Bracket prediction",   "Next-quarter forecast"),
        ("69.3% accuracy",       "Better decisions than gut feel alone"),
    ]

    c.setFillColor(C_NAVY)
    c.rect(40, y - 14 * len(mappings) - 2, W - 80, 14 * len(mappings) + 14, fill=1, stroke=0)

    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(48, y - 10, mappings[0][0])
    c.drawString(W/2 + 10, y - 10, mappings[0][1])
    c.setFillColor(C_MGRAY)
    c.line(40, y - 14, W - 40, y - 14)

    ty = y - 26
    for mm, biz in mappings[1:]:
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 9)
        c.drawString(48, ty, mm)
        c.setFillColor(C_GOLD)
        c.drawString(W/2 + 10, ty, biz)
        c.setStrokeColor(colors.HexColor("#1A3A8F"))
        c.setLineWidth(0.4)
        c.line(40, ty - 4, W - 40, ty - 4)
        ty -= 14

    y = ty - 20

    # Business pipeline
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "THE SAME PIPELINE — ANY INDUSTRY")
    y -= 8

    d = business_use_case_diagram(W - 80, 80)
    renderPDF.draw(d, c, 40, y - 80)
    y -= 98

    # Three key takeaways
    c.setFillColor(C_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "THREE THINGS TO REMEMBER")
    y -= 12

    takeaways = [
        (C_NAVY,   "01", "ML IS NOT MAGIC",
         "It is statistics at scale. If you can explain your problem as 'given these inputs,\n"
         "predict this output', ML can probably help."),
        (C_BLUE,   "02", "DATA QUALITY IS EVERYTHING",
         "Our model's best input (seed) is also its most carefully curated. In your business,\n"
         "invest in data quality before investing in algorithms."),
        (C_ORANGE, "03", "START SIMPLE",
         "Our model is not deep learning. It is a Random Forest — a 20-year-old algorithm.\n"
         "You do not need GPT-4 to get 70% accuracy on most business problems."),
    ]
    for bg, num, title, body in takeaways:
        c.setFillColor(bg)
        c.roundRect(40, y - 65, W - 80, 58, 5, fill=1, stroke=0)
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(56, y - 40, num)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(90, y - 20, title)
        c.setFont("Helvetica", 9)
        ty2 = y - 36
        for line in body.split("\n"):
            c.drawString(90, ty2, line)
            ty2 -= 12
        y -= 76

    c.showPage()


def build_page8(c, S):
    """Glossary + Back Cover"""
    c.setFillColor(C_NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Header
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40, H - 30, "SECTION 07  ·  QUICK REFERENCE")
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, H - 54, "GLOSSARY & QUICK REFERENCE")

    y = H - 76

    terms = [
        ("Algorithm",        "A set of rules a computer follows to solve a problem."),
        ("Training",         "Showing the model thousands of historical examples so it learns patterns."),
        ("Feature",          "A single measurable input (e.g. win percentage, seed number)."),
        ("Random Forest",    "500 decision trees that each vote on the answer. Majority wins."),
        ("Decision Tree",    "A flowchart of IF/THEN questions that splits data into groups."),
        ("Accuracy",         "% of predictions the model gets correct on unseen data."),
        ("Log Loss",         "How confident and correct the model is. Lower is better. (Ours: 0.57)"),
        ("Overfitting",      "Model memorises training data but fails on new data. We avoid this with test splits."),
        ("Blending/Ensemble","Combining multiple models or signals to get a better result than any one alone."),
        ("Feature Importance","How much each input contributes to the model's decisions."),
        ("Seed",             "NCAA ranking from 1 (best) to 16 (weakest) within each region."),
        ("Head-to-Head",     "Whether two teams played each other during the regular season."),
    ]

    c.setFillColor(colors.HexColor("#0A2878"))
    c.roundRect(40, y - len(terms) * 20 - 10, W - 80, len(terms) * 20 + 14, 4, fill=1, stroke=0)

    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, y - 10, "TERM")
    c.drawString(185, y - 10, "PLAIN-ENGLISH DEFINITION")
    c.setStrokeColor(C_MGRAY)
    c.setLineWidth(0.4)
    c.line(40, y - 14, W - 40, y - 14)

    ty = y - 24
    for term, defn in terms:
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(50, ty, term)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 8.5)
        c.drawString(185, ty, defn)
        c.setStrokeColor(colors.HexColor("#1A3A8F"))
        c.setLineWidth(0.3)
        c.line(40, ty - 5, W - 40, ty - 5)
        ty -= 20

    y = ty - 20

    # Closing block
    c.setFillColor(C_RED)
    c.rect(40, y - 90, W - 80, 84, fill=1, stroke=0)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W/2, y - 20, "WANT TO BUILD YOUR OWN?")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, y - 38, "The full source code for this project is open source.")
    c.drawCentredString(W/2, y - 52, "Visit the Dead Reckoning site to explore the live bracket,")
    c.drawCentredString(W/2, y - 66, "read the methodology, and fork the code on GitHub.")
    c.setFillColor(C_GOLD)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W/2, y - 82, "github.com/gmashini/march-madness-2026")

    # Bottom decoration
    c.setFillColor(C_GOLD)
    c.rect(0, 34, W, 6, fill=1, stroke=0)
    draw_page_footer(c, 8)

    c.showPage()


# ── MAIN ──────────────────────────────────────────────────────────────────────

def generate():
    output_path = "/Users/georgemashini/dev/dead-reckoning-site/march-madness/ML_Explained_MarchMadness_2026.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle("Machine Learning Explained Through March Madness 2026")
    c.setAuthor("Dead Reckoning")
    c.setSubject("Business ML Explainer — NCAA Tournament Bracket Prediction")

    S = make_styles()

    build_cover(c)
    build_page2(c, S)
    build_page3(c, S)
    build_page4(c, S)
    build_page5(c, S)
    build_page6(c, S)
    build_page7(c, S)
    build_page8(c, S)

    c.save()
    print(f"PDF saved: {output_path}")
    return output_path


if __name__ == "__main__":
    generate()
