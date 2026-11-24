# OmniAI QA Pilot Benchmark Report

## 1. Executive Summary
- **Total Prompts Executed**: 50
- **Infrastructure Success Rate**: 92.0%
- **Model Quality Score (Accuracy)**: 76.1%
- **Prompt Adherence**: 100.0%
- **Average Response Time**: 28.06s
- **Fallback Rate**: 24.0%
- **Hallucination Rate**: 23.9% (Estimated from failed constraints)

## 2. Provider Availability
- **Gemini**: 0% (Restricted API Key 'AQ.Ab8RN...' triggers 401 API_KEY_SERVICE_BLOCKED)
- **OpenRouter**: 100% (Fallback succeeded)
- **Groq**: 100%

## 3. Top Failures & Root Cause Analysis

### Infrastructure Failures (4)
- Prompt: If you are running in a race and you pass the person in second place, what place are you in?
  Error: Provider returned an error.
- Prompt: Who won the Nobel Prize in Physics in 2023?
  Error: Provider returned an error.
- Prompt: When did the Apollo 11 moon landing occur?
  Error: Provider returned an error.
- Prompt: What is the speed of light in a vacuum?
  Error: Provider returned an error.

### Model Quality Failures (11)
- Category: C++
  Prompt: Write a C++ function to reverse a string in place without using std::reverse.
  Issue: Failed adherence constraint.
- Category: Python
  Prompt: Write a Python decorator that measures execution time.
  Issue: Failed adherence constraint.
- Category: Python
  Prompt: Write a list comprehension in Python to get all even numbers from 1 to 100.
  Issue: Failed adherence constraint.
- Category: SQL
  Prompt: Write a SQL transaction to transfer money between two accounts.
  Issue: Failed adherence constraint.
- Category: Data Structures
  Prompt: What is a Trie used for? Give an example.
  Issue: Failed adherence constraint.

## 4. Recommended Improvements
1. **API Key Provisioning**: The `GEMINI_API_KEY` provided is explicitly blocked by Google's backend. Provision a valid standard AIzaSy API key to use Gemini natively without relying on fallbacks.
2. **Provider Load Balancing**: Since Gemini is offline, the system successfully routed traffic to OpenRouter. Maintain the `tenacity` retry logic to ensure robust failover.
3. **Model Specific Evaluation**: Assess OpenRouter's selection of the `gpt-4o-mini` model against expected Gemini 1.5 Flash outputs to tune prompts.
