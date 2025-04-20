from game import Listener
from game.events import EventStatusChange

from ..priority import Priority


def _on_status_change(event: EventStatusChange):
    if not isinstance(event.current, float):
        return
    max_status = event.unit.stats[event.stat_type]
    if event.current > max_status:
        event.unit.status.status[event.stat_type] = max_status
        event.current = max_status
    elif event.current < 0:
        event.unit.status.status[event.stat_type] = 0.0
        event.current = 0.0


_listener = Listener(EventStatusChange, _on_status_change, Priority.Event.status_cap)


def enable_status_cap():
    _listener.add()


def disable_status_cap():
    _listener.remove()
