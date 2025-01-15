from typing import List, Tuple
import json
from prompts import EMOTIONAL_APPEAL_SYSTEM_PROMPT
from utils import check_disclaimer

def generate_emotional_appeal_step(round_number: int, goal: str, history_a: List[str], response: str, attacker_generate) -> Tuple[str, str]:
    """
    Generate the next step in the emotional_appeal jailbreak sequence.
    """
    # Format the conversation history
    history = []
    for i in range(len(history_a)):
        history.append({"role": "assistant", "content": history_a[i]})
        
    # Generate the next step using the attacker model
    result = attacker_generate(
        EMOTIONAL_APPEAL_SYSTEM_PROMPT.format(conversationObjective=goal),
        history,
        response
    )
    
    # Parse the result
    result = json.loads(result)
    return result["generatedQuestion"], result["lastResponseSummary"]

def run(goal: str, attacker_generate, target_generate) -> List[str]:
    """
    Run the emotional_appeal jailbreak.
    """
    print("Starting emotional_appeal")
    history_a = []  # Attacker history
    history_t = []  # Target history
    
    round_number = 0
    while round_number < 5:
        # Generate the next question
        prompt, response_summary = generate_emotional_appeal_step(round_number, goal, history_a, history_t[-1] if history_t else "", attacker_generate)
        
        # Get response from target
        response = target_generate(prompt)
        
        # Check if target refused
        if check_disclaimer(response):
            break
            
        # Update histories
        history_a.append(prompt)
        history_t.append(response)
        round_number += 1
        
    return history_t