from google import genai
try:
    client = genai.Client(vertexai=True, location="us-central1")
    response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
    print("SUCCESS:", response.text)
except Exception as e:
    print("FAILED:", e)
