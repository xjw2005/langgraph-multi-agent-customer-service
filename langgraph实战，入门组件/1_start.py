from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class HelloState(TypedDict):
    name: str
    greeting: str

# define a node
def greet(state: HelloState) -> HelloState:
    name = state['name']
    return {"greeting": f"Hello, {name}!"}

def add_emoji(state: HelloState) -> HelloState:
    greeting = state['greeting']
    return {"greeting": f"{greeting} 🚀"}

# define a graph
graph = StateGraph(HelloState)

graph.add_node("greet", greet)
graph.add_node("add_emoji", add_emoji)

graph.add_edge(START, "greet")
graph.add_edge("greet", "add_emoji")
graph.add_edge("add_emoji", END)

# compile the graph
app = graph.compile()

# run the graph
result = app.invoke({"name": "World"})
print(result["greeting"])
from IPython.display import Image, display
try:
    display(Image(app.get_graph(xray=True).draw_png()))
except Exception as e:
    print("Error displaying graph: ", e)