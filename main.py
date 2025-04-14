from dataclasses import dataclass, field
from pathlib import Path

import streamlit as st
import pygates
from streamlit_agraph import agraph, Node, Edge, Config

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

color_mapping = {
    "1": "#00ff00",
    "0": "#ff0000",
    "None": "#eeeeee",
    "player0": "#aaaaaa",
    "player1": "#aaaaaa",
}

points_mapping = {
    "1_1": 25,
    "2_1": 20,
    "2_2": 20,
    "3_1": 12,
    "3_2": 14,
    "3_3": 12,
    "4_1": 5,
    "4_2": 7,
    "4_3": 7,
    "4_4": 5,
    "5_1": 2,
    "5_2": 3,
    "5_3": 4,
    "5_4": 3,
    "5_5": 2,
}


@dataclass
class Gate:
    gate_id: str
    gate_type: str = None


@dataclass
class Signal:
    signal_id: str
    signal_state: str = None


@dataclass
class Grid:
    nodes: list = field(default_factory=list)
    gates: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    nodes_dict: dict = field(default_factory=dict)
    inputs_dict: dict = field(default_factory=dict)

    def set_gatetype(self, id, type, player):
        for gate in self.gates:
            if gate.gate_id == id:
                gate.gate_type = type

        for node in self.nodes:
            if node.id == id:
                node.label = f"{type} ({player.replace('player', '')})"
                node.color = color_mapping[player]

    def get_gatetype(self, id):
        for gate in self.gates:
            if gate.gate_id == id:
                return gate.gate_type

    def rerun_logic(self):
        for level in range(5, 0, -1):  # Levels 5 down to 1
            for i in range(level):
                base_id = f"{level}_{i + 1}"
                gate_id = f"{base_id}_gate"
                signal_id = f"{base_id}_signal"

                gate_obj = next((g for g in self.gates if g.gate_id == gate_id), None)
                gate_type = gate_obj.gate_type if gate_obj else None

                if not gate_type:
                    for node in self.nodes:
                        if node.id == signal_id:
                            node.color = color_mapping["None"]
                    continue  # Skip if no gate type is set

                # Get input node IDs
                input1_id, input2_id = self.inputs_dict.get(signal_id, (None, None))

                # Get the labels (0/1) from the input signal nodes
                input1_color = next((n.color for n in self.nodes if n.id == input1_id), None)
                input2_color = next((n.color for n in self.nodes if n.id == input2_id), None)

                input1 = [k for k, v in color_mapping.items() if v == input1_color][0]
                input2 = [k for k, v in color_mapping.items() if v == input2_color][0]

                if input1 not in ("0", "1") or input2 not in ("0", "1"):
                    continue  # Skip if inputs are not valid binary values

                # Compute the output using the pygates logic
                gate_func = gate_mapping.get(gate_type)
                if gate_func:
                    result = gate_func(int(input1), int(input2))
                    result_str = str(result)

                    # Update the signal node label and color
                    for node in self.nodes:
                        if node.id == signal_id:
                            node.color = color_mapping[result_str]


if "grid" not in st.session_state:
    grid = Grid()
    for level in range(6):
        grid.nodes_dict[level + 1] = []

        if level == 5:
            for i, x in enumerate("100110"):
                grid.nodes_dict[level + 1].append(f"{level + 1}_{i + 1}")
                grid.nodes.append(Node(id=f"{level + 1}_{i + 1}_signal",
                                       label=x,
                                       color=color_mapping[x],
                                       shape="circle",
                                       size=15))  # Signal node is a circle

        else:
            for i in range(level + 1):
                grid.nodes_dict[level + 1].append(f"{level + 1}_{i + 1}")
                grid.nodes.append(Node(id=f"{level + 1}_{i + 1}_gate", shape="square", size=15,
                                       color="#eeeeee"))  # Gate node is a square
                grid.nodes.append(Node(id=f"{level + 1}_{i + 1}_signal", shape="circle", size=15, color="#eeeeee",
                                       label=str(points_mapping[f"{level + 1}_{i + 1}"])))
                grid.edges.append(Edge(source=f"{level + 1}_{i + 1}_gate",
                                       target=f"{level + 1}_{i + 1}_signal"))
                grid.gates.append(Gate(gate_id=f"{level + 1}_{i + 1}_gate"))  # Assign gate for this node
                grid.signals.append(Signal(signal_id=f"{level + 1}_{i + 1}_signal"))  # Assign signal for this node

    for level in range(1, 7):
        for i in range(0, level + 1):
            input1 = f"{level + 1}_{i + 1}_signal"
            input2 = f"{level + 1}_{i + 2}_signal"
            output = f"{level}_{i + 1}_gate"
            grid.edges.append(Edge(source=input1, target=output))
            grid.edges.append(Edge(source=input2, target=output))
            grid.inputs_dict[f"{level}_{i + 1}_signal"] = (input1, input2)

    st.session_state.grid = grid

if "player0" not in st.session_state:
    st.session_state.player0 = [i for i in gate_mapping.keys()]

if "player1" not in st.session_state:
    st.session_state.player1 = [i for i in gate_mapping.keys()]

config = Config(width=500,
                height=700,
                directed=True,
                physics=False,
                hierarchical=True,
                direction="DU",
                levelSeparation=50,
                nodeSpacing=75,
                blockShifting=True,
                edgeMinimization=True,
                parentCentralization=True,
                sortMethod="directed")

node_id = agraph(nodes=st.session_state.grid.nodes,
                 edges=st.session_state.grid.edges,
                 config=config)

col1, col2 = st.columns(2)

if node_id and "_gate" in node_id:
    col1.write("Player 0")
    gate_type_player0 = col1.selectbox(label="Choose a logic gate type",
                                       options=st.session_state.player0 + [""],
                                       key="player0_selectbox")

    if col1.button("Set gate type for player 0"):
        if gate_type_player0 == "":
            gate_type_player0 = None
        else:
            st.session_state.player0.remove(gate_type_player0)

        previous_state = st.session_state.grid.get_gatetype(node_id)
        if previous_state:
            st.session_state.player0.append(previous_state)

        st.session_state.grid.set_gatetype(node_id, gate_type_player0, "player0")
        st.session_state.grid.rerun_logic()

        st.rerun()

    col2.write("Player 1")
    gate_type_player1 = col2.selectbox(label="Choose a logic gate type",
                                       options=st.session_state.player1 + [""],
                                       key="player1_selectbox")

    if col2.button("Set gate type for player 1"):
        if gate_type_player1 == "":
            gate_type_player1 = None
        else:
            st.session_state.player1.remove(gate_type_player1)

        previous_state = st.session_state.grid.get_gatetype(node_id)
        if previous_state:
            st.session_state.player1.append(previous_state)

        st.session_state.grid.set_gatetype(node_id, gate_type_player1, "player1")
        st.session_state.grid.rerun_logic()

        st.rerun()

st.info("Click on a gate (square) and select the gate type from the select box below.")
st.info("Each player has one set of gates. Player 0 is red, player 1 is green.")
st.info("You can remove a gate from the board and place it somewhere else.")
st.info("The game ends when a player places it's last gate on the board.")
