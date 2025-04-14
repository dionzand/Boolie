from dataclasses import dataclass, field
import streamlit as st
import pygates
from streamlit_agraph import agraph, Node, Edge, Config
import networkx

lg = pygates.Gates

st.set_page_config(
    layout="wide"
)

gate_mapping = {
    "AND": lg.AND,
    "NAND": lg.NAND,
    "OR": lg.OR,
    "XOR": lg.XOR,
    "NOR": lg.NOR,
    "XNOR": lg.XNOR,
}


@dataclass
class Gate:
    gate_id: str
    gate_type: str = None


@dataclass
class Grid:
    nodes: list = field(default_factory=list)
    gates: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    nodes_dict: dict = field(default_factory=dict)
    inputs_dict: dict = field(default_factory=dict)

    def set_gatetype(self, id, type):
        for gate in self.gates:
            if gate.gate_id == id:
                gate.gate_type = type

        for node in self.nodes:
            if node.id == id:
                node.label = type

    def rerun_logic(self):
        for level in range(5, 0, -1):  # Levels 5 down to 1
            for i in range(level):
                node_id = f"{level}_{i + 1}"
                gate_obj = next((g for g in self.gates if g.gate_id == node_id), None)
                gate_type = gate_obj.gate_type if gate_obj else None

                if not gate_type:
                    continue  # Skip if no gate type is set

                # Get input node IDs
                input1_id, input2_id = self.inputs_dict[node_id]

                # Get the labels (0/1) from the input nodes
                input1 = next((n.label for n in self.nodes if n.id == input1_id), None)
                input2 = next((n.label for n in self.nodes if n.id == input2_id), None)

                if input1 not in ("0", "1") or input2 not in ("0", "1"):
                    continue  # Skip if inputs are not valid binary values

                # Compute the output using the pygates logic
                gate_func = gate_mapping.get(gate_type)
                if gate_func:
                    result = gate_func(int(input1), int(input2))
                    result_str = str(result)

                    # Update the node label and color
                    for node in self.nodes:
                        if node.id == node_id:
                            node.label = result_str
                            node.color = color_mapping[result_str]

color_mapping = {
    "1": "green",
    "0": "black"
}

if "grid" not in st.session_state:
    grid = Grid()
    for level in range(6):
        grid.nodes_dict[level + 1] = []

        if level == 5:
            for i, x in enumerate("100110"):
                grid.nodes_dict[level + 1].append(f"{level + 1}_{i + 1}")
                grid.nodes.append(Node(id=f"{level + 1}_{i + 1}",
                                       label=x,
                                       color=color_mapping[x],
                                       shape="circle"))  # Signal node is a circle

        else:
            for i in range(level):
                grid.nodes_dict[level + 1].append(f"{level + 1}_{i + 1}_gate")
                grid.nodes.append(Node(id=node_id, shape="square"))  # Gate node is a square
                grid.gates.append(Gate(gate_id=node_id))  # Assign gate for this node

            for i in range(int(level / 2) + 1):
                node_id = f"{level + 1}_{i + 1}"
                grid.nodes.append(Node(id=node_id, shape="circle"))  # Signal node is a circle



    for level in range(1, 12):
        for i in range(level):
            if level % 2 == 0:
                grid.edges.append(Edge(source=f"{level + 1}_{i + 1}",
                                       target=f"{level}_{i + 1}"))
            else:
                grid.edges.append(Edge(source=f"{level + 1}_{i + 1}",
                                       target=f"{level}_{i + 1}"))
                grid.edges.append(Edge(source=f"{level + 1}_{i + 2}",
                                       target=f"{level}_{i + 1}"))
                grid.inputs_dict[f"{level}_{i + 1}"] = (f"{level + 1}_{i + 1}", f"{level + 1}_{i + 2}")


    st.session_state.grid = grid

config = Config(width=2000,
                height=700,
                directed=True,
                physics=False,
                hierarchical=True,
                direction="DU",
                levelSeparation=100,
                nodeSpacing=100,
                blockShifting=True,
                edgeMinimization=True,
                parentCentralization=True,
                sortMethod="directed", )

node_id = agraph(nodes=st.session_state.grid.nodes,
                 edges=st.session_state.grid.edges,
                 config=config)

gate_type = st.selectbox(label="Choose a logic gate type for this node",
                         options=gate_mapping.keys())

if st.button("Set gate type"):
    st.session_state.grid.set_gatetype(node_id, gate_type)
    st.session_state.grid.rerun_logic()
    st.rerun()
