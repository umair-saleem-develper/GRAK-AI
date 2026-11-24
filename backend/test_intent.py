from services.intent_router import detect_intent

test_cases = [
    "Explain photosynthesis",
    "Give me a labeled diagram of a plant",
    "Create a gaming mouse diagram with labeled buttons",
    "Explain this code",
    "What is the speed of light?",
    "write a python function to add two numbers",
    "ek futuristic car ki tasveer banao"
]

for tc in test_cases:
    res = detect_intent(tc)
    print(f'Query: "{tc}" => Intent: {res["intent"]} | Subject: {res["subject"]}')
