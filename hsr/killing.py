from game import Unit, listen

from .events import EventDeath
from .priority import Priority
from .statusmanager import Damage, regenerate_energy

_killing_energy = 10.0


def _on_death(event: EventDeath):
    if isinstance(event.node.source, Damage):
        source_unit = event.node.source.unit
    else:
        source_unit = event.node.get_source(Unit)
        if source_unit is None:
            return
    regenerate_energy(event.node, source_unit, _killing_energy, True)


def set_killing_energy(value: float):
    global _killing_energy
    _killing_energy = value


listen(EventDeath, _on_death, Priority.Event.killing_energy)
