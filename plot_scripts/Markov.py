"""
Markov Chain Analysis for Jailbreak Attack Sequences

This script implements Markov chain analysis to model the progression of jailbreak attacks
through various states. It analyzes the sequential patterns in attack attempts to understand
the probabilistic transitions between different stages of an attack, such as from initial
probing questions to successful jailbreaks.

Key features:
- Construction of Markov transition matrices from attack sequence data
- Probabilistic modeling of attack progression patterns
- Analysis of common attack paths and their likelihood of success
- Identification of critical transition points in successful attacks
- Visualization of attack sequence transition networks
- Statistical metrics on attack progression efficiency

This analysis provides insights into the dynamic nature of multi-turn jailbreak attacks,
helping researchers understand which attack sequences are most likely to progress toward
successful jailbreaks and where defensive measures might be most effective.

Usage:
    python Markov.py [options]

The script outputs transition matrices, visualizations, and statistical analyses that
characterize the nature of successful attack progressions.
"""

import os
import json
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Define the folder and filename pattern
folder = "../results"
file_prefix = "crowding_identity"

# Define state mapping function
def get_state(score):
    if isinstance(score, int):  # Ensure score is valid
        if score == 10:
            return 1  # Score 10
        elif 6 <= score <= 9:
            return 2  # Score 6-9
        elif 2 <= score <= 5:
            return 3  # Score 2-5
        elif score == 1:
            return 4  # Score 1
    return None  # Ignore invalid scores

# Initialize transition storage
transitions = []
file_count = 0  # Counter for processed files

# Process each file in the folder
for filename in os.listdir(folder):
    if filename.startswith(file_prefix) and filename.endswith(".jsonl"):
        file_path = os.path.join(folder, filename)
        file_count += 1  # Count the analyzed file
        
        with open(file_path, "r") as file:
            scores = []
            for line in file:
                data = json.loads(line.strip())
                score = data.get("score")  # Safely get the score
                
                # Handle different types of scores
                if isinstance(score, str) and score.isdigit():
                    score = int(score)
                elif not isinstance(score, int):
                    continue  # Ignore invalid scores
                
                state = get_state(score)
                if state:
                    scores.append(state)
            
            # Process transitions from the extracted scores
            for i in range(len(scores) - 1):
                transitions.append((scores[i], scores[i + 1]))

# Create transition matrix
state_labels = [1, 2, 3, 4]
transition_matrix = pd.DataFrame(0, index=state_labels, columns=state_labels, dtype=float)

for (from_state, to_state) in transitions:
    transition_matrix.loc[from_state, to_state] += 1

# Normalize to get probabilities
transition_matrix = transition_matrix.div(transition_matrix.sum(axis=1), axis=0).fillna(0)

# Display results
print(f"\nTotal files analyzed: {file_count}")
print("\nMarkov Chain Transition Matrix:\n", transition_matrix)

# Define better labels for readability
state_names = {
    1: "10",
    2: "6-9",
    3: "2-5",
    4: "1"
}

# Create Markov Chain graph with properly labeled states
G = nx.DiGraph()

# Add nodes first
for state in state_labels:
    G.add_node(state_names[state])


# Now add edges with proper weights
for i in state_labels:
    for j in state_labels:
        if transition_matrix.loc[i, j] > 0:
            G.add_edge(state_names[i], state_names[j], weight=transition_matrix.loc[i, j])

plt.figure(figsize=(10, 8))
pos = nx.circular_layout(G)  # Ensures even spacing

# Track which pairs of nodes already have curved edges
curved_pairs = set()

# Draw edges and add labels manually
for u, v, data in G.edges(data=True):
    weight = data['weight']
    
    # Determine if reverse edge exists (to create a curve if needed)
    has_reverse = G.has_edge(v, u)
    print(f"u: {u}, v: {v}, weight: {weight}, has reverse: {has_reverse}")
    
    # Handle self-loops separately
    if u == v:
        # Self-loop with large arc
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], 
                              connectionstyle="arc3,rad=2.0", 
                              arrowstyle='-|>', 
                              arrowsize=15,
                              width=1.5, 
                              edge_color="black")
        
        # Add label at the top of the loop
        loop_x, loop_y = pos[u]
        plt.text(loop_x, loop_y + 0.2, f"{weight:.3f}", 
                ha='center', va='center', 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Handle regular edges
    elif has_reverse:
        # Check if we've already drawn a curved edge between these nodes
        rad=-0.1
        curved_pairs
        # Draw curved edge
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], 
                              connectionstyle=f"arc3,rad={rad}", 
                              arrowstyle='<|-', 
                              arrowsize=25,
                              width=2.5, 
                              edge_color="black")
        
        # Calculate position for edge label
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        x_mid = (2*x1 + x2) / 3
        y_mid = (2*y1 + y2) / 3
        
        # Offset label position based on curvature direction
        offset = 0.2
        dx = -(y2 - y1) * offset * rad * 2
        dy = (x2 - x1) * offset * rad * 2
        
        # Add curved edge label
        plt.text(x_mid + dx, y_mid + dy, f"{weight:.3f}", 
                ha='center', va='center', 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
    else:
        # Draw straight edge for one-way
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], 
                              arrowstyle='-|>', 
                              arrowsize=25,
                              width=2.5, 
                              edge_color="black")
        
        # Calculate middle point for label
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        x_mid = (x1 + x2) / 2
        y_mid = (y1 + y2) / 2
        
        # Add straight edge label
        plt.text(x_mid, y_mid, f"{weight:.3f}", 
                ha='center', va='center', 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_size=500, node_color="lightblue")

# Draw node labels
nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

plt.title(f"Markov Chain of Score Transitions ( tactic: {file_prefix} )")
plt.axis('off')  # Turn off axis
plt.tight_layout()
plt.show()
