from bisect import insort_right


class Node:
    def __init__(self, priority=0) -> None:
        self.priority = priority

    def condition(self) -> bool:
        return True

    def run(self):
        pass


class Chain:
    def __init__(self) -> None:
        self.nodes: list[Node] = []
        self.current_node: Node | None = None

    def add(self, node: Node):
        insort_right(self.nodes, node, key=lambda x: x.priority)

    def flush(self):
        while True:
            for node in self.nodes.copy():
                if not node.condition():
                    self.nodes.remove(node)
            if len(self.nodes) == 0:
                break
            self.current_node = self.nodes.pop(0)
            self.current_node.run()
        self.current_node = None
