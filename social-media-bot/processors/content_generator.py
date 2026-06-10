"""Use Claude to generate platform-specific social media content from a transcript."""
import json
import anthropic
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _system_prompt() -> str:
    return f"""You are a world-class social media strategist and copywriter for {config.BRAND_NAME},
a {config.BRAND_NICHE} brand. Your tone is {config.BRAND_VOICE}.

You only write content that is authentic, compliant (no guaranteed-profit claims), and
platform-native. You deeply understand what stops a scroll on each platform."""


def generate_all_platforms(
    transcript: str,
    segments: list[dict],
    video_type: str,
    video_title: str,
    duration_seconds: float,
) -> dict:
    """
    Generate a full content package for all platforms.

    Returns a dict keyed by platform with generated copy and clip suggestions.
    """
    segments_json = json.dumps(segments[:80], indent=2)  # cap to avoid token overload

    prompt = f"""
## Source Video
- Title: {video_title}
- Type: {video_type}  (one of: live_trading, webinar, testimonial, course)
- Duration: {duration_seconds:.0f} seconds
- Brand hashtags: {config.NICHE_HASHTAGS}

## Full Transcript
{transcript[:8000]}

## Transcript Segments (with timestamps)
{segments_json}

---

Generate a complete social media content package in valid JSON using the exact structure below.
For every `clip_suggestion`, pick a real timestamp range from the segments above where the
speaker says something compelling, insightful, or emotional. The clip must be under the
platform's max duration.

Return ONLY the JSON object, no markdown fences.

{{
  "instagram": {{
    "reel": {{
      "hook": "First 3 seconds on-screen text / spoken hook (max 10 words)",
      "caption": "Caption with line breaks, emojis, CTA (max 2200 chars)",
      "hashtags": "30 relevant hashtags",
      "clip_suggestion": {{"start": 0.0, "end": 0.0, "reason": "why this moment"}}
    }},
    "carousel_post": {{
      "slide_texts": ["Slide 1 headline", "Slide 2 text", "Slide 3 text", "Slide 4 text", "Slide 5 CTA"],
      "caption": "Caption for the carousel post",
      "hashtags": "30 relevant hashtags"
    }}
  }},
  "x": {{
    "tweet": {{
      "text": "Single tweet ≤ 280 chars with hook",
      "clip_suggestion": {{"start": 0.0, "end": 0.0, "reason": "why this moment"}}
    }},
    "thread": {{
      "tweets": [
        "1/ Opening tweet that hooks",
        "2/ Next tweet",
        "3/ Next tweet",
        "4/ Next tweet",
        "5/ Closing tweet with CTA"
      ]
    }}
  }},
  "tiktok": {{
    "hook": "Spoken opening line (≤ 3 seconds, creates curiosity)",
    "caption": "TikTok caption with trending sounds note and hashtags",
    "hashtags": "20 trending + niche hashtags",
    "clip_suggestion": {{"start": 0.0, "end": 0.0, "reason": "why this moment"}},
    "b_roll_ideas": ["Idea 1", "Idea 2", "Idea 3"]
  }},
  "youtube": {{
    "short": {{
      "title": "YouTube Short title (≤ 60 chars)",
      "clip_suggestion": {{"start": 0.0, "end": 0.0, "reason": "why this moment"}}
    }},
    "long_form": {{
      "title": "YouTube video title (SEO-optimised, ≤ 70 chars)",
      "description": "Full YouTube description with timestamps, links placeholder, and keywords",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
      "thumbnail_text": "Bold text overlay for thumbnail (≤ 6 words)",
      "chapters": [
        {{"time": "0:00", "label": "Intro"}},
        {{"time": "1:00", "label": "Chapter label"}}
      ]
    }}
  }}
}}
"""

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_system_prompt(),
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if Claude adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw)
