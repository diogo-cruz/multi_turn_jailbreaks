import json
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Load summary data from the jsonl file into a DataFrame
data = []
with open('./results/summary.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))
df = pd.DataFrame(data)

# Ensure proper data types
df['min_score'] = pd.to_numeric(df['min_score'], errors='coerce')
df['min_round'] = pd.to_numeric(df['min_round'], errors='coerce')
df['goal_achieved'] = df['goal_achieved'].fillna(False)

# Create the Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Attack Effectiveness Dashboard"),
    dcc.Tabs(id="tabs", value="tab1", children=[
        dcc.Tab(label="Score Distribution by Turn Type", value="tab1"),
        dcc.Tab(label="Success Rate by Model & Turn Type", value="tab2"),
        dcc.Tab(label="Average min_score by Model & Turn Type", value="tab3"),
        dcc.Tab(label="Histogram of min_round (Multi-Turn)", value="tab4"),
    ]),
    html.Div(id="tabs-content")
])

##############################
# Tab 1: Violin Plot         #
##############################
tab1_layout = html.Div([
    html.H2("Score Distribution by Turn Type"),
    html.Div([
        html.Label("Select Target Model:"),
        dcc.Dropdown(
            id='tab1-model-dropdown',
            options=[{'label': m, 'value': m} for m in sorted(df['target_model'].dropna().unique())],
            multi=True,
            placeholder="Choose model(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block'}),
    html.Div([
        html.Label("Select Jailbreak Tactic:"),
        dcc.Dropdown(
            id='tab1-tactic-dropdown',
            options=[{'label': t, 'value': t} for t in sorted(df['jailbreak_tactic'].dropna().unique())],
            multi=True,
            placeholder="Choose tactic(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block', 'marginLeft': '5%'}),
    dcc.Graph(id='tab1-graph')
])

##############################
# Tab 2: Success Rate        #
##############################
tab2_layout = html.Div([
    html.H2("Success Rate (%) by Target Model and Turn Type"),
    html.Div([
        html.Label("Select Target Model:"),
        dcc.Dropdown(
            id='tab2-model-dropdown',
            options=[{'label': m, 'value': m} for m in sorted(df['target_model'].dropna().unique())],
            multi=True,
            placeholder="Choose model(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block'}),
    html.Div([
        html.Label("Select Jailbreak Tactic:"),
        dcc.Dropdown(
            id='tab2-tactic-dropdown',
            options=[{'label': t, 'value': t} for t in sorted(df['jailbreak_tactic'].dropna().unique())],
            multi=True,
            placeholder="Choose tactic(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block', 'marginLeft': '5%'}),
    dcc.Graph(id='tab2-graph')
])

##############################
# Tab 3: Average min_score    #
##############################
tab3_layout = html.Div([
    html.H2("Average min_score by Target Model and Turn Type"),
    html.Div([
        html.Label("Select Jailbreak Tactic:"),
        dcc.Dropdown(
            id='tab3-tactic-dropdown',
            options=[{'label': t, 'value': t} for t in sorted(df['jailbreak_tactic'].dropna().unique())],
            multi=True,
            placeholder="Choose tactic(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block'}),
    dcc.Graph(id='tab3-graph')
])

##############################
# Tab 4: Histogram of min_round (Multi-Turn) #
##############################
tab4_layout = html.Div([
    html.H2("Histogram of Rounds at which min_score was Achieved (Multi-Turn)"),
    html.Div([
        html.Label("Select Target Model:"),
        dcc.Dropdown(
            id='tab4-model-dropdown',
            options=[{'label': m, 'value': m} for m in sorted(df['target_model'].dropna().unique())],
            multi=True,
            placeholder="Choose model(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block'}),
    html.Div([
        html.Label("Select Jailbreak Tactic:"),
        dcc.Dropdown(
            id='tab4-tactic-dropdown',
            options=[{'label': t, 'value': t} for t in sorted(df['jailbreak_tactic'].dropna().unique())],
            multi=True,
            placeholder="Choose tactic(s)"
        )
    ], style={'width': '45%', 'display': 'inline-block', 'marginLeft': '5%'}),
    dcc.Graph(id='tab4-graph')
])

# Render the selected tab's layout
@app.callback(Output("tabs-content", "children"),
              Input("tabs", "value"))
def render_content(tab):
    if tab == "tab1":
        return tab1_layout
    elif tab == "tab2":
        return tab2_layout
    elif tab == "tab3":
        return tab3_layout
    elif tab == "tab4":
        return tab4_layout

# Tab 1: Violin Plot of min_score by turn_type
@app.callback(
    Output('tab1-graph', 'figure'),
    [Input('tab1-model-dropdown', 'value'),
     Input('tab1-tactic-dropdown', 'value')]
)
def update_tab1(selected_models, selected_tactics):
    filtered_df = df.copy()
    if selected_models:
        filtered_df = filtered_df[filtered_df['target_model'].isin(selected_models)]
    if selected_tactics:
        filtered_df = filtered_df[filtered_df['jailbreak_tactic'].isin(selected_tactics)]
    
    fig = px.violin(
        filtered_df,
        x="turn_type",
        y="min_score",
        color="turn_type",
        points="all",  # Show all individual points
        box=True,      # Overlay a box plot to show quartiles
        title="Distribution of min_score by Turn Type",
        hover_data=["target_model", "jailbreak_tactic"]
    )
    return fig

# Tab 2: Bar Chart of Success Rate grouped by target_model and turn_type
@app.callback(
    Output('tab2-graph', 'figure'),
    [Input('tab2-model-dropdown', 'value'),
     Input('tab2-tactic-dropdown', 'value')]
)
def update_tab2(selected_models, selected_tactics):
    filtered_df = df.copy()
    if selected_models:
        filtered_df = filtered_df[filtered_df['target_model'].isin(selected_models)]
    if selected_tactics:
        filtered_df = filtered_df[filtered_df['jailbreak_tactic'].isin(selected_tactics)]
    
    # Group by target_model and turn_type to compute success rate
    group = filtered_df.groupby(['target_model', 'turn_type']).agg(
        total_cases=('goal_achieved', 'count'),
        successes=('goal_achieved', lambda x: (x == True).sum())
    ).reset_index()
    group['success_rate'] = group['successes'] / group['total_cases'] * 100

    fig = px.bar(
        group,
        x="target_model",
        y="success_rate",
        color="turn_type",
        barmode="group",
        title="Success Rate (%) by Target Model and Turn Type",
        labels={'success_rate': 'Success Rate (%)', 'target_model': 'Target Model'}
    )
    return fig

# Tab 3: Grouped Bar Chart of Average min_score by target_model and turn_type
@app.callback(
    Output('tab3-graph', 'figure'),
    [Input('tab3-tactic-dropdown', 'value')]
)
def update_tab3(selected_tactics):
    filtered_df = df.copy()
    if selected_tactics:
        filtered_df = filtered_df[filtered_df['jailbreak_tactic'].isin(selected_tactics)]
    
    group = filtered_df.groupby(['target_model', 'turn_type']).agg(
        avg_score=('min_score', 'mean')
    ).reset_index()
    
    fig = px.bar(
        group,
        x="target_model",
        y="avg_score",
        color="turn_type",
        barmode="group",
        title="Average min_score by Target Model and Turn Type",
        labels={'avg_score': 'Average min_score', 'target_model': 'Target Model'}
    )
    return fig

# Tab 4: Histogram of min_round (Multi-Turn Attacks)
@app.callback(
    Output('tab4-graph', 'figure'),
    [Input('tab4-model-dropdown', 'value'),
     Input('tab4-tactic-dropdown', 'value')]
)
def update_tab4(selected_models, selected_tactics):
    # Filter to only multi-turn attacks and ensure min_round exists
    filtered_df = df[(df['turn_type'] == 'multi') & (df['min_round'].notna())].copy()
    if selected_models:
        filtered_df = filtered_df[filtered_df['target_model'].isin(selected_models)]
    if selected_tactics:
        filtered_df = filtered_df[filtered_df['jailbreak_tactic'].isin(selected_tactics)]
    
    fig = px.histogram(
        filtered_df,
        x="min_round",
        nbins=10,
        color="target_model",
        title="Histogram of Rounds at which min_score was Achieved (Multi-Turn)",
        labels={'min_round': 'Round at min_score'}
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
