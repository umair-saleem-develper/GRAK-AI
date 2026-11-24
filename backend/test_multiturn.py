import time
import os
from services.ai_engine import generate_text_stream

def run_multiturn_test(num_turns=10):
    messages = []
    print(f"\n--- Starting {num_turns}-Turn Multi-Turn Role Conversion Test ---")
    
    for turn in range(1, num_turns + 1):
        user_prompt = f"Turn {turn}: Say exactly 'Hello {turn}'."
        messages.append({"role": "user", "content": user_prompt})
        
        print(f"\n[Prompt {turn}] -> {user_prompt}")
        
        assistant_reply = ""
        try:
            for chunk in generate_text_stream(messages):
                # Ignore emojis that crash windows printing
                assistant_reply += chunk
        except Exception as e:
            print(f"\n[FATAL] Stream crashed on turn {turn}: {e}")
            return False
            
        print(f"[Reply {turn}] <- {assistant_reply.strip().encode('ascii', 'ignore').decode('ascii')}")
        
        if "[Error:" in assistant_reply:
            print(f"\n[FATAL] Provider error detected on turn {turn}. The multi-turn role test failed.")
            return False
            
        # Append as "model" role, mimicking the frontend behavior
        messages.append({"role": "model", "content": assistant_reply})
        
        # Wait a moment to avoid rapid-fire rate limits
        time.sleep(2)

    print(f"\n--- SUCCESS: Completed all {num_turns} turns without a role validation crash! ---")
    return True

if __name__ == "__main__":
    success = run_multiturn_test(10)
    if not success:
        exit(1)
