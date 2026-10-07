import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import numpy as np
from networkx.algorithms.community import greedy_modularity_communities

st.set_page_config(page_title="My Network App", layout="wide")

# 1. Load the Karate Club Graph
G = nx.karate_club_graph()

# Calculate communities
communities = list(greedy_modularity_communities(G))
community_dict = {}
for comm_id, comm in enumerate(communities):
    for node in comm:
        community_dict[node] = comm_id

# Calculate centralities
degree_dict = dict(G.degree())
betweenness_dict = nx.betweenness_centrality(G)

# Add properties to nodes
for n in G.nodes():
    G.nodes[n]["community"] = community_dict[n]
    G.nodes[n]["degree"] = degree_dict[n]
    G.nodes[n]["betweenness"] = betweenness_dict[n]

# 2. Sidebar controls
st.sidebar.header("Settings")

# Change layout
layout_option = st.sidebar.selectbox(
    "Select Layout",
    ["Spring (Force-Directed)", "Circular"]
)

# Change node size
size_option = st.sidebar.selectbox(
    "Size Nodes By",
    ["Degree", "Betweenness Centrality"]
)

# Filter by degree threshold
min_degree = st.sidebar.slider("Minimum Degree", min_value=1, max_value=17, value=1)

# k-core filter for the extra challenge
k_filter = st.sidebar.slider("k-Core Filter (Simplify hairball)", min_value=0, max_value=5, value=0)

# Filter the graph
filtered_nodes = [n for n in G.nodes() if G.degree[n] >= min_degree]
sub_G = G.subgraph(filtered_nodes).copy()

if k_filter > 0:
    try:
        sub_G = nx.k_core(sub_G, k=k_filter)
    except:
        sub_G = nx.Graph()

# 3. Compute layout coordinates
if layout_option == "Circular":
    pos = nx.circular_layout(sub_G)
else:
    pos = nx.spring_layout(sub_G, seed=42)

# Prepare edge lines for Plotly
edge_x = []
edge_y = []
for edge in sub_G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    mode="lines",
    line=dict(width=1, color="#888"),
    hoverinfo="none"
)

# Prepare node points for Plotly
node_x = []
node_y = []
node_colors = []
node_sizes = []
node_text = []

for n in sub_G.nodes():
    node_x.append(pos[n][0])
    node_y.append(pos[n][1])
    node_colors.append(sub_G.nodes[n]["community"])

    # Scale node sizes so they look good on screen
    if size_option == "Degree":
        node_sizes.append(sub_G.nodes[n]["degree"] * 2 + 10)
    else:
        node_sizes.append(sub_G.nodes[n]["betweenness"] * 70 + 10)

    node_text.append(
        f"Node {n}<br>Degree: {sub_G.nodes[n]['degree']}<br>Community: {sub_G.nodes[n]['community']}"
    )

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    text=[str(n) for n in sub_G.nodes()],
    textposition="top center",
    hovertext=node_text,
    hoverinfo="text",
    marker=dict(
        color=node_colors,
        size=node_sizes,
        colorscale="Viridis",
        line=dict(width=1, color="black")
    )
)

fig_network = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        title="Node-Link Diagram",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
)

# 4. Adjacency Matrix (Extra challenge)
sorted_nodes = sorted(sub_G.nodes(), key=lambda n: sub_G.nodes[n]["community"])
if len(sorted_nodes) > 0:
    matrix = nx.to_numpy_array(sub_G, nodelist=sorted_nodes)
    labels = [str(n) for n in sorted_nodes]

    fig_matrix = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            colorscale="Blues",
            showscale=False
        )
    )
    fig_matrix.update_layout(
        title="Adjacency Matrix (Sorted by Community)",
        yaxis=dict(autorange="reversed")
    )
else:
    fig_matrix = go.Figure()

# 5. Display charts in Streamlit
st.title("Zachary's Karate Club Network Explorer")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_network, use_container_width=True)
with col2:
    st.plotly_chart(fig_matrix, use_container_width=True)

# 6. Required Write-up
st.markdown("---")
st.header("Project Overview & Notes")

st.markdown("""
### What this network represents
This dataset is **Zachary's Karate Club**, a classic social network of 34 members in a university karate club. An argument occurred between the club administrator (Node 0) and the instructor (Node 33), causing the club to split into two separate factions.

### Why I chose these encodings
- **Node Color:** Represents the **detected community** (faction). This clearly shows the split between the administrator's group and the instructor's group.
- **Node Size:** Represents **degree or betweenness centrality**. Sizing by degree shows who talks to the most people, while sizing by betweenness highlights the "bridge" people connecting the two sides.

### One limitation
The layout can be misleading. Force-directed diagrams place nodes using simulated spring forces, not real geographic distances. Viewers might assume nodes placed close together in 2D space are mathematically identical, or that nodes placed near the center of the canvas are inherently more important than peripheral ones.

### Layout trade-offs & the hairball problem
- **Force-Directed vs. Circular:** The force-directed layout separates factions cleanly into spatial clusters. The circular layout spreads nodes evenly, eliminating overlaps, but makes it hard to see natural groups because links cross the middle in a web.
- **Node-Link vs. Adjacency Matrix:** The node-link view makes paths easy to follow. The matrix view completely stops edges from overlapping, making dense community blocks visible along the diagonal.
- **The Hairball Problem:** When networks grow large, links tangle into an unreadable "hairball." Using the **k-core filter** strips out outer leaf nodes and leaves only the densely connected central core, making the core structure readable again.
""")