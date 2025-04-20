from bisect import insort_left, insort_right
from contextlib import contextmanager


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

    def __getitem__(self, index: int):
        return self.nodes[index]

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, node: Node):
        return node in self.nodes

    def add(self, node: Node, left_most=False):
        if left_most:
            insort_left(self.nodes, node, key=lambda x: x.priority)
        else:
            insort_right(self.nodes, node, key=lambda x: x.priority)

    def clear_invalid(self):
        for node in self.nodes.copy():
            if not node.condition():
                self.nodes.remove(node)

    @contextmanager
    def next(self):
        self.current_node = self.nodes.pop(0)
        try:
            yield self.current_node
        finally:
            self.current_node = None

    def flush(self):
        while True:
            self.clear_invalid()
            if len(self.nodes) == 0:
                break
            with self.next() as node:
                yield node
