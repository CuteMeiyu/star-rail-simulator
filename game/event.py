from bisect import insort_right
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")


class Listener:
    def __init__(self, event_type: type[_T], callback: Callable[[_T], Any], priority=0) -> None:
        self.event_type = event_type
        self.callback = callback
        self.priority = priority

    def remove(self):
        remove_listener(self)


class Event:
    listener: Listener | None = None
    halt: bool = False


listeners: list[Listener] = []


def listen(event_type: type[_T], callback: Callable[[_T], Any], priority=0) -> Listener:
    listener = Listener(event_type, callback, priority)
    add_listener(listener)
    return listener


def add_listener(listener: Listener):
    insort_right(listeners, listener, key=lambda x: x.priority)


def remove_listener(listener: Listener):
    listeners.remove(listener)


def trigger(event: Event):
    for listener in listeners.copy():
        if isinstance(event, listener.event_type):
            original_listener = event.listener
            event.listener = listener
            listener.callback(event)
            event.listener = original_listener
            if event.halt:
                break
