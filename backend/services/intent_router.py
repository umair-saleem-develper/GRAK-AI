import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Intent Constants
INTENT_CODE = "code"
INTENT_IMAGE_GENERATION = "image_generation"
INTENT_VISUAL_EXPLANATION = "visual_explanation"
INTENT_TEXT = "text_answer"

# Regex patterns for quick classification
CODE_PATTERNS = [
    r"\b(write|create|debug|fix|explain|review|analyze|refactor|test)\s+(the\s+|this\s+|that\s+|my\s+)?(code|function|script|class|query|regex|algorithm|program)\b",
    r"\b(python|javascript|typescript|c\+\+|java|golang|rust|php|sql|html|css)\b.*(code|function|script|example|snippet)",
    r"```[a-zA-Z]*\n[\s\S]*?\n```",
    r"\bdef\s+[a-zA-Z_]\w*\(",
    r"\bfunction\s+[a-zA-Z_]\w*\(",
    r"\bclass\s+[a-zA-Z_]\w*[:\{]",
    r"\b(syntax\s+error|nullpointerexception|traceback|undefined\s+is\s+not\s+a\s+function|typeerror|attributeerror)\b"
]

IMAGE_GEN_PATTERNS = [
    r"\b(generate|create|draw|make|paint|render|produce)\s+(an?\s+)?(image|picture|photo|pic|artwork|illustration|drawing|render)\b",
    r"\b(create|generate|draw|design|render)\s+(a\s+)?(gaming\s+mouse|futuristic|anime|fantasy|portrait|wallpaper|concept\s+art|logo|banner)\b",
    r"\b(create|generate|draw)\s+(an?\s+)?(labeled\s+)?diagram\s+(of|for|with)\b",
    r"\b(image|picture|tasveer|tasvir|drawing|pic)\s*(banao|bana\s+do|generate\s+karo|create\s+karo|banayein)\b",
    r"\b(tasveer|tasvir|image)\s+banaiye\b",
    r"(تصویر بنائیں|تصویر بناؤ|ڈائیگرام بنائیں|فوٹو بناؤ)"
]

VISUAL_EXPLANATION_PATTERNS = [
    r"\b(with|accompanied\s+by)\s+(a\s+)?(labeled\s+)?diagram\b",
    r"\b(labeled\s+diagram|cross\s+section|anatomy\s+diagram|structure\s+diagram)\b",
    r"\b(give|show|fetch|display)\s+(me\s+)?(a\s+|an\s+|the\s+|its\s+)?(pic|photo|image|diagram)\b",
    r"\b(give|show)\s+.*?\b(pic|photo|image|diagram)\b.*?\b(explain|parts|all\s+part)\b",
    r"\b(explain\s+all\s+parts?|parts?\s+of)\b",
    r"\b(diagram\s+of\s+(a\s+)?(plant|heart|cell|solar\s+system|eye|brain|atom|flower|engine))\b",
    r"\b(diagram|tasveer|tasvir)\s+(ke\s+saath|k\s+sath)\s*(samjhao|batao|explain)\b",
    r"\b(plant|heart|solar\s+system|cell)\s+diagram\b",
    r"\b(diagram|tasveer|photo|pic)\s*(dikhao|do|batao|bhejo)\b",
    r"(ڈائیگرام کے ساتھ|تصویر دکھاؤ|ڈائیگرام دکھاؤ)"
]

def resolve_context_subject(query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """If the query is a brief follow-up, extract the subject from previous messages."""
    if not history:
        return query
    
    # Exclude the current message from history if present at the end
    prior_history = history[:-1] if len(history) > 1 and history[-1].get("content", "").strip() == query.strip() else history
    if not prior_history:
        return query

    clean_q = query.strip().lower()
    words = clean_q.split()
    
    followup_cues = ["is ka", "iska", "iski", "inke", "it", "its", "this", "that", "same", "ab", "now", "previous"]
    is_followup = len(words) <= 6 or any(cue in clean_q for cue in followup_cues)
    
    if is_followup:
        # Search prior messages for a user question or topic
        for msg in reversed(prior_history[-6:]):
            content = msg.get("content", "")
            if content and not content.startswith(":::") and len(content.strip()) > 2:
                first_line = content.split("\n")[0][:80]
                cleaned_subj = re.sub(r"^(what is|explain|tell me about|who is|samjhao|batao)\s+", "", first_line, flags=re.I)
                cleaned_subj = cleaned_subj.strip(" ?.!:")
                if cleaned_subj and len(cleaned_subj) > 2 and cleaned_subj.lower() not in [c.lower() for c in followup_cues]:
                    return f"{cleaned_subj} {query}"
                    
    return query

def detect_intent(query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Classifies the user query into:
    - INTENT_CODE: Programming and code queries
    - INTENT_IMAGE_GENERATION: Requests to generate new images or diagrams with AI
    - INTENT_VISUAL_EXPLANATION: Educational topics requesting diagrams or photos
    - INTENT_TEXT: General questions, concepts, math, explanations
    """
    if not query or not query.strip():
        return {"intent": INTENT_TEXT, "subject": "", "prompt": ""}

    resolved_query = resolve_context_subject(query, history)
    lower = resolved_query.lower()

    # 1. Code intent check
    for pat in CODE_PATTERNS:
        if re.search(pat, lower):
            return {
                "intent": INTENT_CODE,
                "subject": query,
                "prompt": resolved_query
            }

    # 2. Image generation intent check (Explicit "create/generate/draw image")
    for pat in IMAGE_GEN_PATTERNS:
        if re.search(pat, lower):
            clean_prompt = re.sub(
                r"\b(generate|create|draw|make|paint|render|produce|an?|the|image|picture|photo|pic|artwork|illustration|drawing|tasveer|tasvir|banao|bana\s+do|generate\s+karo|create\s+karo|banayein)\b",
                "",
                query,
                flags=re.IGNORECASE
            )
            clean_prompt = re.sub(r"\s+", " ", clean_prompt).strip(" ?.!:") or query
            is_diagram = "diagram" in lower or "schematic" in lower
            return {
                "intent": INTENT_IMAGE_GENERATION,
                "subject": clean_prompt,
                "prompt": clean_prompt,
                "is_diagram": is_diagram
            }

    # 3. Visual explanation check (Explanation with labeled diagram / photos)
    for pat in VISUAL_EXPLANATION_PATTERNS:
        if re.search(pat, lower):
            clean_topic = re.sub(
                r"\b(give|me|an?|the|of|labeled|diagrams?|photos?|pics?|images?|show|with|explain|and|tell|ke\s+saath|samjhao|dikhao|do|batao|bhejo)\b", 
                "", 
                query, 
                flags=re.IGNORECASE
            )
            clean_topic = re.sub(r"\s+", " ", clean_topic).strip(" ?.!:") or query
            return {
                "intent": INTENT_VISUAL_EXPLANATION,
                "subject": clean_topic.title(),
                "prompt": resolved_query
            }

    # 4. Default: pure text answer (e.g. "Explain photosynthesis", "What is physics", "Who is Einstein")
    return {
        "intent": INTENT_TEXT,
        "subject": query,
        "prompt": resolved_query
    }
