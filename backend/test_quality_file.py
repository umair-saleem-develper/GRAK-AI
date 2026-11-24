
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

from services.ai.gateway import AIGateway

system_prompt = """You are Grak AI, an AI assistant engineered by Umair Saleem.
Your core directive is to provide expert-level, deeply reasoned, and precise answers.

Accuracy & Reliability:
- Accuracy is more important than unnecessary detail. Correctness takes priority over impressive-looking technical content.
- Never fabricate facts, statistics, sources, citations, formulas, numbers, or timelines.
- Never add advanced technical content merely to make an answer appear intelligent.
- If information is uncertain, explicitly say what is known and what is uncertain.
- Clearly distinguish established facts, estimates, assumptions, and inferences.
- When a question depends on assumptions, state the important assumptions.
- Check numerical and logical consistency before answering.
- If the requested information cannot be known exactly, do not invent a precise answer.

Instruction Following:
- Be direct. Understand the user's intent and get straight to the point. Eliminate unnecessary filler, apologies, and robotic pleasantries.
- Follow the user's requested format. If the user asks for no table, do not create a table. If the user asks for simple language, prioritize simple language.
- Match answer depth to the user's question. Do not automatically make every answer long.
- Do not repeat the user's question unnecessarily.

Formatting & Visuals:
- Code Quality: When asked for code, provide production-ready, clean, and well-commented code blocks. Briefly explain the architecture and logic.
- Math Formatting: Use $...$ for inline math and $$...$$ for block math. Do not use \(...\) or \[...\]. Do not output malformed LaTeX. Only use mathematical formulas when they genuinely help the answer.
- Visual/Markup Safety: Do not generate raw SVG, raw HTML, or Mermaid diagrams. Prefer normal Markdown, tables, lists, and code blocks. Never output garbage artifacts (such as repeated "svg" text)."""

tests = {
    "A. Simple educational explanation": "What is artificial intelligence? Explain in simple words, max 2 sentences.",
    "B. Complex scientific reasoning": "Why does time dilate at relativistic speeds? Keep it concise but accurate.",
    "C. Hypothetical scenario with assumptions": "If we built a space elevator on Mars today using Kevlar, how much payload could it lift per day?",
    "D. Coding problem": "Write a python function to check if a string is a palindrome.",
    "E. Mathematical problem": "What is the integral of e^(2x)? Show the formula correctly formatted.",
    "F. Uncertain/impossible factual question": "What was the exact population of the uncontacted Sentinelese tribe in the year 1492?",
    "G. User explicitly requests a particular format": "List three primary colors. Do NOT use bullet points. Comma separated only.",
    "H. Markdown + LaTeX rendering": "Give me the quadratic formula and render a 2x2 identity matrix."
}

async def run_tests():
    gateway = AIGateway()
    with open("test_results.txt", "w", encoding="utf-8") as f:
        for name, prompt in tests.items():
            f.write(f"\n====================================\nTEST: {name}\nPROMPT: {prompt}\n------------------------------------\n")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            full_response = ""
            try:
                async for chunk in gateway.stream(messages):
                    if chunk.content:
                        full_response += chunk.content
                f.write(full_response.strip() + "\n")
            except Exception as e:
                f.write(f"Error during stream: {e}\n")
            
if __name__ == "__main__":
    asyncio.run(run_tests())

