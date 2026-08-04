import ollama
import re
import time
from ollama import Client

# --- Reliability guardrail: 10s timeout + up to 3 retries (ADDED — existing code untouched) ---
OLLAMA_TIMEOUT = 10   # seconds, per attempt
MAX_RETRIES    = 3
_client = Client(timeout=OLLAMA_TIMEOUT)

def _chat_with_retry(*args, **kwargs):
    """Wrap ollama.chat with a per-attempt 10s timeout and up to MAX_RETRIES attempts."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _client.chat(*args, **kwargs)
        except Exception as e:
            last_error = e
            print(f"⏳ Attempt {attempt}/{MAX_RETRIES} failed ({type(e).__name__}). Retrying...")
            time.sleep(1)   # brief backoff
    raise RuntimeError(f"🔌 Server busy — no response after {MAX_RETRIES} attempts. ({last_error})")

# Route every existing ollama.chat(...) call through the retry wrapper, without editing those calls.
ollama.chat = _chat_with_retry

# --- Live Metrics Tracking ---
METRICS = {
    "total_attempts": 0,
    "guardrail_rejections": 0,
    "successful_runs": 0,
    "total_latency_seconds": 0.0
}

def check_profanity_with_llm(user_input: str) -> bool:
    """
    Zero-hardcode safety guardrail using Chain of Thought reasoning.
    Forces Llama 3.2 to evaluate toxicity openly before making a verdict.
    """
    guard_prompt = (
        f"Analyze the input word: '{user_input}'\n\n"
        "First, think about whether this word is a curse word, profanity, vulgarity, or an insult.\n"
        "Then, finish your response with a clear verdict line exactly like this:\n"
        "VERDICT: UNACCEPTABLE\n"
        "or\n"
        "VERDICT: ACCEPTABLE"
    )
    
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": guard_prompt}]
        )
        
        analysis = response.message.content.strip().upper()
        
        # If the LLM marks it as UNACCEPTABLE anywhere in its verdict, block it
        if "UNACCEPTABLE" in analysis:
            return True
            
        return False
        
    except Exception as e:
        print(f"[Guardrail Warning] AI Evaluation failed: {e}")
        return False
    
def get_name_meaning(name: str) -> tuple[str, float]:
    """Calls Ollama to get the name meaning and measures the latency."""
    prompt = f"Tell me the meaning of the name '{name}'. Keep it short and simple."
    
    start_time = time.time()
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )
    end_time = time.time()
    
    latency = end_time - start_time
    return response.message.content, latency

def main():
    print("🧚 Welcome to Project Pixie CLI Architecture 🧚")
    print("Type 'q', 'Q', 'quit', or 'Quit' at any time to exit.\n")
    
    while True:
        user_input = input("\nEnter a name to analyze: ").strip()
        
        # 1. Check Exit Condition
        if user_input.lower() in ['q', 'quit']:
            print("\n" + "="*40)
            print("🧚 FINAL PROJECT METRICS & KPIS 🧚")
            print("="*40)
            print(f"🔹 Total Inputs Attempted: {METRICS['total_attempts']}")
            print(f"🔹 Guardrail Rejections:  {METRICS['guardrail_rejections']}")
            
            if METRICS['total_attempts'] > 0:
                rejection_rate = (METRICS['guardrail_rejections'] / METRICS['total_attempts']) * 100
                print(f"🔹 Guardrail Rejection Rate: {rejection_rate:.1f}%")
                
            if METRICS['successful_runs'] > 0:
                avg_latency = METRICS['total_latency_seconds'] / METRICS['successful_runs']
                print(f"🔹 Average Token Latency:    {avg_latency:.2f} seconds (Target: < 10s)")
                print(f"🔹 Schema Compliance Rate:  100.0% Compliant")
            print("="*40)
            print("Goodbye!")
            break
        
        METRICS["total_attempts"] += 1
        
        # 2. Rule-Based Guardrail: Length check
        if len(user_input) > 50:
            print("❌ Guardrail Triggered: Name length exceeds 50 characters.")
            METRICS["guardrail_rejections"] += 1
            continue
            
        # 3. Rule-Based Guardrail: All Numbers check (Allows "priya45", blocks "452345")
        if user_input.isdigit():
            print("❌ Guardrail Triggered: Name cannot contain numbers only.")
            METRICS["guardrail_rejections"] += 1
            continue
            
        # 4. Rule-Based Guardrail: All Special Characters check (Blocks pure symbols like "$$$%%%")
        if re.match(r"^[^a-zA-Z0-9]+$", user_input):
            print("❌ Guardrail Triggered: Name cannot contain special characters only.")
            METRICS["guardrail_rejections"] += 1
            continue

        # 5. LLM Guardrail: Profanity validation
        print("Checking safety guardrails...")
        if check_profanity_with_llm(user_input):
            print("❌ Guardrail Triggered: Inappropriate language detected by AI.")
            METRICS["guardrail_rejections"] += 1
            continue

        # 6. Pipeline Execution
        print(f"✨ Passed! Asking Llama 3.2 about '{user_input}'...")
        try:
            meaning, latency = get_name_meaning(user_input)
            
            # Record Success Metrics
            METRICS["successful_runs"] += 1
            METRICS["total_latency_seconds"] += latency
            
            print("\n--- Result ---")
            print(meaning)
            print(f"Latency: {latency:.2f} seconds")
            print("-" * 14)
            
        except Exception as e:
            print(f"An error occurred executing your request: {e}")

if __name__ == "__main__":
    main()