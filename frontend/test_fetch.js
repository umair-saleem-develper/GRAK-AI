async function test() {
  const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2YjdiMzc5Yi1lNTlkLTRjZDUtOTFkNC03N2ZhZjE4MTRmNzAiLCJleHAiOjE3ODY3Mzk1NjEsImp0aSI6IjAzNzRjZGVhLTkxM2EtNDg4Ni1iYjZiLWJmYThlOWQ1MmY4YyJ9.pwosEhdI2QRC65efJkgIeMNyMEThnxqGzwYGjV-SWjk';
  console.log("Connecting to proxy...");
  try {
    const response = await fetch('http://localhost:3000/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content: "Hello node test" })
    });
    
    console.log("Response ok:", response.ok, "Status:", response.status);
    
    if (!response.ok) {
      console.log("Error body:", await response.text());
      return;
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    
    const start = Date.now();
    let streamDone = false;
    while (!streamDone) {
      const { value, done } = await reader.read();
      if (done) {
        streamDone = true;
        break;
      }
      const text = decoder.decode(value, { stream: true });
      console.log(`[${Date.now() - start}ms] CHUNK:`, JSON.stringify(text));
    }
    console.log("Stream closed natively.");
  } catch(e) {
    console.error("Fetch failed:", e);
  }
}
test();
