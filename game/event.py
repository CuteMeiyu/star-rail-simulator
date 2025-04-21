from bisect import insort_right
from types import UnionType
from typing import Any, Callable, TypeVar, overload

_T = TypeVar("_T")


class Listener:
    @overload
    def __init__(self, event_type: type[_T], callback: Callable[[_T], Any], priority=0) -> None: ...
    @overload
    def __init__(self, event_type: UnionType, callback: Callable, priority=0) -> None: ...

    def __init__(self, event_type: type[_T] | UnionType, callback: Callable, priority=0) -> None:
        self.event_type = event_type
        self.callback = callback
        self.priority = priority

    def add(self):
        insort_right(listeners, self, key=lambda x: x.priority)

    def remove(self):
        listeners.remove(self)


class Event:
    listener: Listener | None = None
    halt: bool = False


listeners: list[Listener] = []


@overload
def listen(event_type: type[_T], callback: Callable[[_T], Any], priority=0) -> Listener: ...
@overload
def listen(event_type: UnionType, callback: Callable, priority=0) -> Listener: ...


def listen(event_type: type[_T] | UnionType, callback: Callable[[_T], Any] | Callable, priority=0) -> Listener:
    listener = Listener(event_type, callback, priority)
    listener.add()
    return listener


def trigger(event: Event):
    for listener in listeners.copy():
        if isinstance(event, listener.event_type):
            original_listener = event.listener
            event.listener = listener
            listener.callback(event)
            event.listener = original_listener
            if event.halt:
                break
