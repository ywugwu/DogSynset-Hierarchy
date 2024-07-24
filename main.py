import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import collections

weights = collections.defaultdict(float)
for file in os.listdir('weights/'):
    if file.endswith('.json') and 'all_' not in file:
        with open(f'weights/{file}') as f:
            data = json.load(f)      
            for name in data:
                weights[name.lower()] = data[name]['type_3_text_consistency_score'] + data[name]['type_2_text_consistency_score'] + data[name]['type_3_text_consistency_score']
# apply min max scaling
minv = min(weights.values())
maxv = max(weights.values())
weights = {
    name: (score - minv) / (maxv - minv)
    for name, score in weights.items()
}

# use wide layout
st.set_page_config(layout="wide")
# set title
st.title("DogSynset Tree Visualization")

class Node:
    def __init__(self, id, label, shape, size, value):
        self.id = id
        self.label = label
        self.shape = shape
        self.size = size
        self.value = value  # Add value attribute

class Edge:
    def __init__(self, source, target):
        self.source = source
        self.target = target

# Load JSON data
with open('dog_breed_tree.json') as f:
    data = json.load(f)

nodes = []
edges = []
vis = {}
values_at_depth = collections.defaultdict(list)
def dfs(node,depth):
    if node['name'].lower() in weights:
        values_at_depth[depth].append(weights[node['name'].lower()])
    # if len(vis) >= 512:  # Limit the number of nodes for clarity
    #     return
    node['id'] = node['name']
    if node['id'] not in vis:
        # random_value = np.random.rand()  # Assign a random value between 0 and 1
        vis[node['id']] = True
        nodes.append(
            Node(
                id=node['id'],
                label=node['name'].split(',')[0],
                shape="dot",
                size=25,
                value=weights.get(node['name'].lower(), -1.0)  # Get value from weights dictionary
            )
        )
    if 'children' in node:
        
        for child in node['children']:
            child['id'] = child['name']
            edges.append(
                Edge(
                    source=node['id'],
                    target=child['id'],
                )
            )
            dfs(child,depth+1)

dfs(data,0)

# scatter plot of values at each depth: (depth, value1), (depth, value2), ...
fig, ax = plt.subplots()
for depth, values in values_at_depth.items():
    ax.scatter([depth] * len(values), values, c='b', alpha=0.5)
ax.set_xlabel('Depth')
ax.set_ylabel('Value')
ax.set_title('Consistency Score Distribution at Each Depth')
# save the plot
plt.savefig('consistency_score_distribution.png')


st.header(f"Please Wait for the Rendering of {len(nodes)} nodes and {len(edges)} edges to Complete:coffee:...")
st.header(f"Green = High Score, Red = Low Score, Gray = N/A")
# Convert Python objects to JavaScript-readable format
nodes_js = [{'id': n.id, 'label': n.label, 'shape': n.shape, 'size': n.size, 'value': n.value} for n in nodes]
edges_js = [{'from': e.source, 'to': e.target} for e in edges]

def get_color(value):
    if value == -1:
        return '#808080'  # Gray for undefined values
    elif value >= 0:
        # Mapping from 0 to 1 (Red to Green in RGB)
        return mcolors.rgb2hex((1 - value, value, 0))
    else:
        # Default to gray if something unexpected
        return '#808080'

# Generate colors using the custom function
values = [node.value for node in nodes]
colors = [get_color(value) for value in values]

# Include color in nodes_js
for node, color in zip(nodes_js, colors):
    node['color'] = color

nodes_json = json.dumps(nodes_js)
edges_json = json.dumps(edges_js)

html_string = f"""
<html>
<head>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
  <div id="mynetwork" style="height: 800px; width: 100%;"></div>
  <script type="text/javascript">
    var nodes = new vis.DataSet({json.dumps(nodes_js)});
    var edges = new vis.DataSet({json.dumps(edges_js)});
    var container = document.getElementById('mynetwork');
    var data = {{
        nodes: nodes,
        edges: edges
    }};
    var options = {{
        layout: {{
            hierarchical: {{
                enabled: true,
                direction: 'LR',  // Left to Right
                sortMethod: 'hubsize' //'directed'  // Direct sorting to maintain direction
            }}
        }},
        nodes: {{
            shape: 'dot',
            font: {{
                size: 15
            }},
            color: '{{node.color}}'  // Ensure each node color is set from node attributes
        }},
        edges: {{
            width: 2
        }}
    }};
    var network = new vis.Network(container, data, options);
  </script>
</body>
</html>
"""


st.components.v1.html(html_string, height=800)
