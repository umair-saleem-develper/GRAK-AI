import asyncio
import json
import re
from services.image_search import (
    search_web_images, 
    search_icon_image, 
    build_fallback_image_url, 
    verify_image_url
)

VISUAL_TRIGGER_WORDS = [
    "diagram", "diagrams", "labeled diagram", "parts of", "anatomy",
    "structure", "cross section", "how it works", "process flow",
    "tasveer ke sath", "tasweer ke sath", "diagram ke sath", "diagram do",
    "with diagram", "show diagram", "visual explanation"
]


def should_trigger_visuals(query: str) -> bool:
    q = (query or "").lower().strip()
    return any(word in q for word in VISUAL_TRIGGER_WORDS)


async def get_visual_enrichment(query: str, gateway, history: list[dict] = None) -> dict | None:
    """
    Extracts the topic and process details for ChatGPT-style visual breakdown:
    1. Hero: Labeled parts diagram
    2. Process: Inputs, process diagram, outputs
    3. Main parts: 4-6 concise parts
    """
    recent_context = ""
    if history:
        trimmed = history[-6:]
        lines = []
        for msg in trimmed:
            role = msg.get("role", "user")
            content = (msg.get("content") or "")[:300]
            lines.append(f"{role.upper()}: {content}")
        recent_context = "\n".join(lines)

    extraction_prompt = f"""You are an educational topic and diagram architect for Grak AI.
Recent Conversation History:
{recent_context if recent_context else "(New conversation)"}

Current User Message: "{query}"

Instructions:
1. Identify the core topic (e.g., Plant, Human Heart, Solar System, Cell, Engine). If current message is a follow-up ("is ka diagram do", "show pic"), retrieve the topic from the history!
2. If there is NO recognizable topic in either message or history, return {{"needs_clarification": true}}.
3. Identify the main process associated with the topic (e.g., for Plant -> Photosynthesis; for Heart -> Blood Circulation; for Car Engine -> Four-Stroke Combustion).
4. Provide 2-3 input ingredients with single-word or short names (e.g. ["Sunlight", "Water", "Carbon Dioxide"]), the process name, and 1-2 output results (e.g. ["Glucose", "Oxygen"]).
5. List 4 to 6 main physical parts of the topic with concise 5-10 word functions.

Output ONLY valid JSON in this exact structure:
{{
  "needs_clarification": false,
  "topic": "Plant",
  "emoji": "🌱",
  "hero_query": "plant parts labeled diagram",
  "process_name": "Photosynthesis",
  "process_question": "How Does a Plant Make Food?",
  "process_query": "photosynthesis diagram light reaction",
  "inputs": ["Sunlight", "Water", "Carbon dioxide"],
  "outputs": ["Glucose", "Oxygen"],
  "parts": [
    {{"name": "Roots", "function": "Absorb water and minerals from the soil"}},
    {{"name": "Stem", "function": "Transports nutrients and supports the plant"}},
    {{"name": "Leaves", "function": "Capture sunlight and produce food"}},
    {{"name": "Flowers", "function": "Help in reproduction and seed production"}}
  ]
}}"""

    try:
        res = await gateway.chat([{"role": "user", "content": extraction_prompt}], apply_identity=False)
        raw_text = (res.content or "").strip()
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if not json_match:
            return None
        parsed = json.loads(json_match.group(0))
        if parsed.get("needs_clarification"):
            return {"needs_clarification": True}

        topic = parsed.get("topic") or query.title()
        emoji = parsed.get("emoji") or "🌱"
        hero_query = parsed.get("hero_query") or f"{topic} parts labeled diagram"
        process_name = parsed.get("process_name") or "Process"
        process_question = parsed.get("process_question") or f"How Does {topic} Work?"
        process_query = parsed.get("process_query") or f"{topic} {process_name} process diagram"
        raw_inputs = parsed.get("inputs") or ["Input 1", "Input 2"]
        raw_outputs = parsed.get("outputs") or ["Output 1"]
        parts = parsed.get("parts") or []

        # Parallel search: Hero Image, Process Diagram, and Input/Output icons
        hero_task = search_web_images(hero_query, count=1, is_hero=True)
        process_task = search_web_images(process_query, count=1, is_hero=False)
        input_tasks = [search_icon_image(inp) for inp in raw_inputs[:3]]
        output_tasks = [search_icon_image(out) for out in raw_outputs[:2]]

        gathered = await asyncio.gather(
            hero_task,
            process_task,
            *input_tasks,
            *output_tasks,
            return_exceptions=True
        )

        hero_res = gathered[0]
        process_res = gathered[1]
        input_icons_res = gathered[2: 2 + len(input_tasks)]
        output_icons_res = gathered[2 + len(input_tasks):]

        hero_img = (
            hero_res[0]
            if isinstance(hero_res, list) and hero_res
            else {
                "url": build_fallback_image_url(f"{topic} parts labeled diagram", 900, 550),
                "title": f"{topic} — Labeled Diagram",
                "source": "Grak Visuals",
                "source_url": "https://images.google.com",
            }
        )

        process_img = (
            process_res[0]
            if isinstance(process_res, list) and process_res
            else {
                "url": build_fallback_image_url(f"{process_name} educational process diagram", 700, 400),
                "title": process_name,
                "source": "Grak Visuals",
                "source_url": "https://images.google.com"
            }
        )

        input_icons = []
        for idx, item in enumerate(input_icons_res):
            if isinstance(item, dict) and item.get("url"):
                input_icons.append(item)
            else:
                name = raw_inputs[idx] if idx < len(raw_inputs) else f"Input {idx+1}"
                input_icons.append({"name": name, "url": build_fallback_image_url(name, 160, 160)})

        output_icons = []
        for idx, item in enumerate(output_icons_res):
            if isinstance(item, dict) and item.get("url"):
                output_icons.append(item)
            else:
                name = raw_outputs[idx] if idx < len(raw_outputs) else f"Output {idx+1}"
                output_icons.append({"name": name, "url": build_fallback_image_url(name, 160, 160)})

        return {
            "needs_clarification": False,
            "topic": topic,
            "emoji": emoji,
            "hero": hero_img,
            "process_name": process_name,
            "process_question": process_question,
            "process_image": process_img,
            "inputs": input_icons,
            "outputs": output_icons,
            "parts": parts,
        }
    except Exception as e:
        print(f"[visual_enrichment] Error: {e}")
        return None


def build_visual_system_prompt(enrichment: dict | None) -> str:
    if not enrichment:
        return ""

    if enrichment.get("needs_clarification"):
        return """IMPORTANT: The user asked for an explanation with a diagram without naming a topic, and there is no topic in the previous messages.
Politely ask them (in their language, Roman Urdu or English) which topic they would like to explore with a diagram (suggest 2-3 examples like Plant, Human Heart, or Solar System)."""

    topic = enrichment["topic"]
    emoji = enrichment.get("emoji", "🌱")
    hero = enrichment["hero"]
    proc_q = enrichment.get("process_question", f"How Does {topic} Work?")
    proc_img = enrichment.get("process_image", {})
    inputs = enrichment.get("inputs", [])
    outputs = enrichment.get("outputs", [])
    parts = enrichment.get("parts", [])

    # Format inputs for visual-flow block
    # format: inputs=Name|url,Name|url
    inps_str = ",".join([f"{i['name']}|{i['url']}" for i in inputs])
    outs_str = ",".join([f"{o['name']}|{o['url']}" for o in outputs])
    proc_str = f"{proc_img.get('title', enrichment.get('process_name'))}|{proc_img.get('url')}"

    # Sample parts list formatting
    parts_formatted = []
    for idx, p in enumerate(parts[:6]):
        parts_formatted.append(f"{idx+1}. **{p['name']}**: {p['function']}")
    parts_guide = "\n".join(parts_formatted) if parts_formatted else f"1. **Part 1**: Concise one-line function\n2. **Part 2**: Concise one-line function"

    return f"""CRITICAL FORMAT INSTRUCTION FOR VISUAL EXPLANATION:
The user is asking for a visual explanation with a diagram.
You MUST output the answer following this EXACT ChatGPT-style layout in this strict order:

1. Title line with ONE emoji + topic + "Explanation with Diagram" (e.g. `### {emoji} {topic} — Explanation with Diagram`).
2. One short intro paragraph (max 2 sentences, bold only the key term).
3. Heading `### 1. Diagram of a {topic}` followed IMMEDIATELY by this exact block:
:::visual-hero
image: {hero['url']}
title: {topic} — Labeled Diagram
source: {hero.get('source', 'Google Images')}
source_url: {hero.get('source_url', '')}
:::
4. A short numbered list of the main parts. Each item MUST be **bold name** + colon + one-line function (max 12 words).
Example:
{parts_guide}

5. Heading `### 2. {proc_q}` followed IMMEDIATELY by this exact flow block:
:::visual-flow
inputs: {inps_str}
process: {proc_str}
outputs: {outs_str}
:::
Followed by 1–2 clear sentences explaining how the process works in simple terms.

6. Heading `### 3. Why Is {topic} Important?` with 4–5 short bullet points.
7. A final line starting with `**In short:**` (one sentence summary).

STRICT NEGATIVE CONSTRAINTS:
- Do NOT output colored "How it works / Key role" component cards.
- Do NOT output any "Growth Equation" blockquote.
- Do NOT output comparison tables.
- Do NOT ask any follow-up question at the end.
- Use clean, consistent white/light gray text; bold only key terms.
- Match user language: If Roman Urdu, translate headings and explanations to Roman Urdu (keep technical terms in English).
"""
