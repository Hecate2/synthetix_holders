import json
from decimal import Decimal
import networkx as nx
# import matplotlib.pyplot as plt

graph = nx.DiGraph()
with open('transfer.txt', 'r') as f:
    for line in f:
        transfer = json.loads(line)
        from_address: str = transfer['Data']['From']
        if from_address not in graph:
            graph.add_node(from_address, weight=0)
        to_address: str = transfer['Data']['To']
        if to_address not in graph:
            graph.add_node(to_address, weight=0)
        transfer_value: int = transfer['Data']['Value']
        graph.nodes[from_address]['weight'] -= transfer_value
        graph.nodes[to_address]['weight'] += transfer_value
        if edge := graph.get_edge_data(from_address, to_address):
            edge['weight'] += transfer_value
        else:
            graph.add_edge(from_address, to_address, weight=transfer_value)

print(f'{graph.number_of_nodes()} nodes')
# print(graph.nodes.data())
print(f'{graph.number_of_edges()} edges')
# print(graph.edges.data())
node_and_weight = [(node, graph.nodes[node]['weight']) for node in graph.nodes]
node_and_weight.sort(key=lambda i: abs(i[1]), reverse=True)
print(node_and_weight)
with open('sUSD-balance-by-transfer.txt', 'w') as f:
    for i in node_and_weight:
        f.write(f'{i[0]}, {Decimal(i[1])/10**18}\n')

# d = dict(graph.degree)
# color_map = []
# for node in graph.nodes:
#     if abs(graph.nodes[node]['weight']) > 1e18/100:
#         color_map.append('red')
#     else:
#         color_map.append('skyblue')

# pos = nx.spring_layout(graph, seed=68)
# fig = plt.figure()
# timer = fig.canvas.new_timer(interval=10000)
# timer.add_callback(plt.close)
# nx.draw(graph, pos, with_labels=True, node_color=color_map, node_shape="o", linewidths=1,
#         font_size=2, font_color="black", edge_color="grey",
#         nodelist=d.keys(), node_size=[(v + 5) * 5 for v in d.values()])
# plt.savefig('nodes.eps', bbox_inches='tight')
# timer.start()
# plt.show()
