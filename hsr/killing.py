from game import Unit, listen

from .events import EventDeath
from .priority import Priority
from .statusmanager import Damage, regenerate_energy


def _on_death(event: EventDeath):
    if isinstance(event.node.source, Damage):
        source_unit = event.node.source.unit
    else:
        source_unit = event.node.get_source(Unit)
        if source_unit is None:
            return
    regenerate_energy(event.node, source_unit, source_unit.battle.context.get("killing_energy", 10.0), True)


listen(EventDeath, _on_death, Priority.Event.killing_energy)
