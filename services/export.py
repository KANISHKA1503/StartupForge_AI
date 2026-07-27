import json
import os


SLIDE_COLORS = [
    "#1a1a2e", "#16213e", "#0f3460", "#1a1a2e",
    "#16213e", "#0f3460", "#1a1a2e", "#16213e",
    "#0f3460", "#1a1a2e", "#16213e", "#0f3460",
]

ACCENT_COLORS = [
    "#e94560", "#00b4d8", "#7b2d8b", "#f0a500",
    "#06d6a0", "#118ab2", "#e94560", "#00b4d8",
    "#7b2d8b", "#f0a500", "#06d6a0", "#118ab2",
]


def export_pitch_deck_html(pitch_deck: dict, output_path: str = "pitch_deck.html") -> str:
    """
    Converts a structured JSON pitch deck into a beautiful standalone HTML file.
    No external dependencies — opens directly in any browser.
    Returns the absolute path to the generated file.
    """
    if not isinstance(pitch_deck, dict):
        raise ValueError("pitch_deck must be a dict")

    startup_name = pitch_deck.get("startup_name", "Startup")
    tagline = pitch_deck.get("tagline", "")
    slides = pitch_deck.get("slides", [])

    slides_html = ""
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        slide_num = slide.get("slide_number", i + 1)
        title = slide.get("title", f"Slide {slide_num}")
        bullets = slide.get("bullet_points", [])
        bg = SLIDE_COLORS[i % len(SLIDE_COLORS)]
        accent = ACCENT_COLORS[i % len(ACCENT_COLORS)]

        bullets_html = "".join(
            f'<li><span class="bullet-dot" style="color:{accent}">▸</span>{b}</li>'
            for b in bullets if isinstance(b, str)
        )

        slides_html += f"""
        <div class="slide" style="background:{bg};">
            <div class="slide-inner">
                <div class="slide-number" style="color:{accent};">0{slide_num}</div>
                <h2 class="slide-title" style="color:{accent};">{title}</h2>
                <ul class="bullets">{bullets_html}</ul>
            </div>
            <div class="slide-footer">
                <span class="footer-name">{startup_name}</span>
                <span class="footer-slide">{slide_num} / {len(slides)}</span>
            </div>
        </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{startup_name} — Investor Pitch Deck</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Inter', sans-serif;
      background: #0a0a1a;
      color: #fff;
      overflow-x: hidden;
    }}

    /* ── HERO ── */
    .hero {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #0f3460 100%);
      padding: 60px 40px;
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      width: 600px; height: 600px;
      background: radial-gradient(circle, rgba(233,69,96,0.15) 0%, transparent 70%);
      top: -100px; right: -100px;
      border-radius: 50%;
    }}
    .hero::after {{
      content: '';
      position: absolute;
      width: 400px; height: 400px;
      background: radial-gradient(circle, rgba(0,180,216,0.12) 0%, transparent 70%);
      bottom: -80px; left: -80px;
      border-radius: 50%;
    }}
    .hero-badge {{
      display: inline-block;
      background: rgba(233,69,96,0.15);
      border: 1px solid rgba(233,69,96,0.4);
      color: #e94560;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 3px;
      text-transform: uppercase;
      padding: 8px 20px;
      border-radius: 100px;
      margin-bottom: 32px;
      position: relative; z-index: 1;
    }}
    .hero-name {{
      font-size: clamp(3rem, 8vw, 6rem);
      font-weight: 800;
      letter-spacing: -2px;
      background: linear-gradient(135deg, #fff 0%, #e94560 50%, #00b4d8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      line-height: 1.1;
      position: relative; z-index: 1;
    }}
    .hero-tagline {{
      font-size: clamp(1rem, 2.5vw, 1.4rem);
      color: rgba(255,255,255,0.6);
      font-weight: 300;
      max-width: 700px;
      margin: 24px auto 0;
      line-height: 1.6;
      position: relative; z-index: 1;
    }}
    .hero-scroll {{
      position: absolute;
      bottom: 40px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      color: rgba(255,255,255,0.3);
      font-size: 0.7rem;
      letter-spacing: 2px;
      text-transform: uppercase;
      z-index: 1;
      animation: bounce 2s infinite;
    }}
    @keyframes bounce {{
      0%, 100% {{ transform: translateX(-50%) translateY(0); }}
      50% {{ transform: translateX(-50%) translateY(6px); }}
    }}

    /* ── SLIDES ── */
    .slides-container {{
      display: flex;
      flex-direction: column;
    }}
    .slide {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 80px 10%;
      position: relative;
      overflow: hidden;
      transition: all 0.3s ease;
    }}
    .slide::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, transparent, currentColor, transparent);
      opacity: 0.3;
    }}
    .slide-inner {{
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      max-width: 900px;
    }}
    .slide-number {{
      font-size: 5rem;
      font-weight: 800;
      opacity: 0.12;
      line-height: 1;
      margin-bottom: 16px;
      font-variant-numeric: tabular-nums;
    }}
    .slide-title {{
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 700;
      letter-spacing: -1px;
      margin-bottom: 48px;
      line-height: 1.1;
    }}
    .bullets {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    .bullets li {{
      font-size: clamp(1rem, 2vw, 1.3rem);
      color: rgba(255,255,255,0.85);
      font-weight: 400;
      line-height: 1.5;
      display: flex;
      align-items: flex-start;
      gap: 16px;
      padding: 20px 24px;
      background: rgba(255,255,255,0.04);
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.06);
      transition: all 0.2s ease;
    }}
    .bullets li:hover {{
      background: rgba(255,255,255,0.07);
      transform: translateX(4px);
    }}
    .bullet-dot {{
      font-size: 1.1rem;
      margin-top: 2px;
      flex-shrink: 0;
    }}
    .slide-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 40px;
      border-top: 1px solid rgba(255,255,255,0.08);
      color: rgba(255,255,255,0.3);
      font-size: 0.8rem;
      font-weight: 500;
      letter-spacing: 1px;
    }}
    .footer-name {{ text-transform: uppercase; letter-spacing: 2px; }}

    /* ── THANK YOU ── */
    .thankyou {{
      min-height: 60vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      background: linear-gradient(135deg, #0a0a1a, #1a1a2e);
      padding: 80px 40px;
    }}
    .thankyou h2 {{
      font-size: clamp(2rem, 6vw, 4rem);
      font-weight: 800;
      background: linear-gradient(135deg, #e94560, #00b4d8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 16px;
    }}
    .thankyou p {{
      color: rgba(255,255,255,0.4);
      font-size: 1rem;
      letter-spacing: 1px;
    }}
    .generated-tag {{
      margin-top: 48px;
      font-size: 0.7rem;
      color: rgba(255,255,255,0.2);
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
  </style>
</head>
<body>

  <!-- HERO COVER SLIDE -->
  <section class="hero">
    <div class="hero-badge">Investor Pitch Deck</div>
    <h1 class="hero-name">{startup_name}</h1>
    <p class="hero-tagline">{tagline}</p>
    <div class="hero-scroll">↓ scroll</div>
  </section>

  <!-- CONTENT SLIDES -->
  <div class="slides-container">
{slides_html}
  </div>

  <!-- THANK YOU -->
  <section class="thankyou">
    <h2>Thank You</h2>
    <p>{startup_name} · {tagline}</p>
    <div class="generated-tag">Generated by HackArena 2.0 · Autonomous Startup AI</div>
  </section>

</body>
</html>"""

    abs_path = os.path.abspath(output_path)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[EXPORT] Pitch deck saved → {abs_path}")
    return abs_path


if __name__ == "__main__":
    sample = {
        "startup_name": "MeetBot AI",
        "tagline": "Turning every meeting into a searchable, actionable knowledge base",
        "slides": [
            {"slide_number": i, "title": t, "bullet_points": [f"Point A about {t}", f"Point B with data {i*10}%", f"Point C strategic note"]}
            for i, t in enumerate(["Problem", "Solution", "Why Now", "Market Opportunity", "Target Market",
                                   "Product Demo", "Competitive Advantage", "Business Model", "Financial Projections",
                                   "Traction & Validation", "Go-to-Market Strategy", "Investment Ask"], 1)
        ]
    }
    path = export_pitch_deck_html(sample)
    print(f"Open: file:///{path}")
