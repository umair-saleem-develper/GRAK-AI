import os
import sys
import json
import time
import ast
from io import StringIO

# Add current dir to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.ai_engine import generate_text_stream, validate_dependencies, check_provider_health

PROMPTS = [
    # C++
    {"cat": "C++", "text": "Write a C++ class for a Bank Account with deposit and withdraw methods. Use modern C++.", "req": "```cpp"},
    {"cat": "C++", "text": "Write a C++ function to reverse a string in place without using std::reverse.", "req": "```cpp"},
    {"cat": "C++", "text": "Create a C++ template class for a simple Stack.", "req": "```cpp"},
    {"cat": "C++", "text": "Show how to use std::unique_ptr in C++ with a custom deleter.", "req": "unique_ptr"},
    {"cat": "C++", "text": "Write a C++ program that reads a file line by line.", "req": "ifstream"},
    
    # Python
    {"cat": "Python", "text": "Write a Python decorator that measures execution time.", "req": "def wrapper"},
    {"cat": "Python", "text": "Write a Python script to fetch data from an API using requests.", "req": "requests.get"},
    {"cat": "Python", "text": "Create a Python class representing a Car with properties and methods.", "req": "class Car"},
    {"cat": "Python", "text": "Write a list comprehension in Python to get all even numbers from 1 to 100.", "req": "[x"},
    {"cat": "Python", "text": "How do you handle exceptions in Python? Show a try-except-finally block.", "req": "finally:"},

    # Java
    {"cat": "Java", "text": "Write a Java Singleton class using thread-safe double-checked locking.", "req": "synchronized"},
    {"cat": "Java", "text": "Write a Java program to reverse a linked list.", "req": "Node"},
    {"cat": "Java", "text": "Show how to use Java Streams to filter a list of strings by length.", "req": ".stream()"},
    {"cat": "Java", "text": "Write a Java interface and a class that implements it.", "req": "implements"},
    {"cat": "Java", "text": "How do you read a file in Java using NIO?", "req": "Files.read"},

    # SQL
    {"cat": "SQL", "text": "Write a SQL query to find the second highest salary from an Employee table.", "req": "SELECT"},
    {"cat": "SQL", "text": "Write an INNER JOIN query between Users and Orders tables.", "req": "JOIN"},
    {"cat": "SQL", "text": "How do you create a table in SQL with a Primary Key and Foreign Key?", "req": "FOREIGN KEY"},
    {"cat": "SQL", "text": "Write a SQL query using GROUP BY and HAVING to find departments with more than 5 employees.", "req": "HAVING"},
    {"cat": "SQL", "text": "Write a SQL transaction to transfer money between two accounts.", "req": "COMMIT"},

    # Data Structures
    {"cat": "Data Structures", "text": "Explain the difference between an Array and a Linked List.", "req": "memory"},
    {"cat": "Data Structures", "text": "What is a Hash Table and how does it resolve collisions?", "req": "collision"},
    {"cat": "Data Structures", "text": "Describe the properties of a Binary Search Tree.", "req": "left"},
    {"cat": "Data Structures", "text": "What is a Trie used for? Give an example.", "req": "prefix"},
    {"cat": "Data Structures", "text": "Explain the concept of a Max Heap.", "req": "root"},

    # Algorithms
    {"cat": "Algorithms", "text": "Explain the Time Complexity of QuickSort.", "req": "O(N"},
    {"cat": "Algorithms", "text": "Describe Dijkstra's shortest path algorithm.", "req": "priority queue"},
    {"cat": "Algorithms", "text": "What is Dynamic Programming? Give an example.", "req": "memoization"},
    {"cat": "Algorithms", "text": "Explain the difference between DFS and BFS.", "req": "stack"},
    {"cat": "Algorithms", "text": "How does Binary Search work and what is its time complexity?", "req": "log N"},

    # Mathematics
    {"cat": "Mathematics", "text": "What is the derivative of x^2 + 3x?", "req": "2x + 3"},
    {"cat": "Mathematics", "text": "Solve the equation: 2x + 5 = 15.", "req": "5"},
    {"cat": "Mathematics", "text": "What is the Pythagorean theorem?", "req": "c^2"},
    {"cat": "Mathematics", "text": "Explain what a prime number is.", "req": "divisible"},
    {"cat": "Mathematics", "text": "Calculate the area of a circle with radius 4.", "req": "16"},

    # Logical Reasoning
    {"cat": "Logical Reasoning", "text": "If all bloops are razzies and all razzies are lazzies, are all bloops lazzies?", "req": "Yes"},
    {"cat": "Logical Reasoning", "text": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?", "req": "5 cents"},
    {"cat": "Logical Reasoning", "text": "Some months have 31 days, others have 30. How many have 28?", "req": "All"},
    {"cat": "Logical Reasoning", "text": "If you are running in a race and you pass the person in second place, what place are you in?", "req": "second"},
    {"cat": "Logical Reasoning", "text": "Mary's father has 5 daughters: Nana, Nene, Nini, Nono. What is the name of the fifth daughter?", "req": "Mary"},

    # Research
    {"cat": "Research", "text": "Who won the Nobel Prize in Physics in 2023?", "req": "L'Huillier"},
    {"cat": "Research", "text": "What is the capital of Australia?", "req": "Canberra"},
    {"cat": "Research", "text": "When did the Apollo 11 moon landing occur?", "req": "1969"},
    {"cat": "Research", "text": "Who wrote 'To Kill a Mockingbird'?", "req": "Harper Lee"},
    {"cat": "Research", "text": "What is the largest ocean on Earth?", "req": "Pacific"},

    # General Knowledge
    {"cat": "General Knowledge", "text": "What is the chemical symbol for Gold?", "req": "Au"},
    {"cat": "General Knowledge", "text": "Who painted the Mona Lisa?", "req": "Da Vinci"},
    {"cat": "General Knowledge", "text": "How many continents are there?", "req": "seven"},
    {"cat": "General Knowledge", "text": "What is the speed of light in a vacuum?", "req": "299"},
    {"cat": "General Knowledge", "text": "Who is known as the father of modern physics?", "req": "Einstein"}
]



def run_benchmark():
    print("Validating dependencies...")
    validate_dependencies()
    
    print("Running Provider Health Checks...")
    health = check_provider_health()
    print(f"Health Status: {health}")
    
    if not health.get("Gemini", False) or not health.get("OpenRouter", False):
        print("FAILED: CRITICAL: Gemini or OpenRouter is not healthy. Halting benchmark as requested.")
        return

    results = []
    results_file = os.path.join(os.path.dirname(__file__), "qa_results.json")
            
    print("Starting QA Pilot Benchmark (50 Prompts)...")
    
    consecutive_failures = 0
    for i, p in enumerate(PROMPTS):
        print(f"[{i+1}/50] Testing {p['cat']}...", flush=True)
        
        old_stdout = sys.stdout
        sys.stdout = stdout_capturer = StringIO()
        
        start_time = time.time()
        
        response_chunks = []
        try:
            for chunk in generate_text_stream([{"role": "user", "content": p["text"]}]):
                response_chunks.append(chunk)
        except Exception as e:
            response_chunks.append(f"\n[Exception: {e}]")
            
        latency = time.time() - start_time
        
        sys.stdout = old_stdout
        captured_logs = stdout_capturer.getvalue()
        
        final_response = "".join(response_chunks)
        
        provider = "Unknown"
        fallback_occurred = False
        
        if "Gemini finished" in captured_logs or "Trying provider: Gemini" in captured_logs: provider = "Gemini"
        if "Groq connected" in captured_logs: provider = "Groq"
        if "OpenRouter connected" in captured_logs: provider = "OpenRouter"
        
        if captured_logs.count("Trying provider") > 1:
            fallback_occurred = True
            
        is_empty = (final_response.strip() == "")
        has_error_token = "[Error" in final_response or "[Exception" in final_response or "Rate Limit Exceeded" in final_response
        
        infra_success = not is_empty and not has_error_token
        
        passed = False
        accuracy_score = 0
        adherence_score = 100 if infra_success else "N/A"
        
        has_req = p["req"].lower() in final_response.lower()
        
        if infra_success:
            if has_req:
                passed = True
                accuracy_score = 100
            else:
                passed = False
                accuracy_score = 0
        else:
            # Infrastructure failure - do not reduce model accuracy score, mark as N/A
            passed = False
            accuracy_score = "N/A"
            
        # If rate limited, sleep longer
        if "Rate Limit Exceeded" in captured_logs or "429" in final_response:
            print(f"WARNING: Rate limit hit. Pausing queue for 60 seconds...")
            consecutive_failures += 1
            time.sleep(60 * consecutive_failures)
        else:
            consecutive_failures = 0
            
        if p["cat"] == "Python" and passed:
            try:
                code_blocks = final_response.split("```python")
                if len(code_blocks) > 1:
                    code = code_blocks[1].split("```")[0]
                    ast.parse(code)
            except SyntaxError:
                passed = False
                accuracy_score = 50
                final_response += "\n\n[QA_AUTO_DETECT]: Python SyntaxError"
                
        results.append({
            "category": p["cat"],
            "prompt": p["text"],
            "response": final_response,
            "pass": passed,
            "infra_success": infra_success,
            "accuracy": accuracy_score,
            "adherence": adherence_score,
            "latency": latency,
            "provider": provider,
            "fallback": fallback_occurred
        })
        
        with open(results_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        # Standard queue pacing
        time.sleep(3)
        
    print("Benchmark complete. Results saved to qa_results.json")

if __name__ == "__main__":
    run_benchmark()
