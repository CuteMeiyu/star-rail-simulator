import math
from dataclasses import dataclass
from enum import IntEnum, auto


class Status(IntEnum):
    ADVANCED = auto()
    NORMAL = auto()
    TURN_END = auto()
    DELAYED = auto()


@dataclass
class RunnerData:
    name: str
    default_speed: float
    distance = 0.0
    status = Status.NORMAL
    no_print = False
    previous_action_value = -1.0


class Runner:
    def __init__(self, runner_name: str, default_speed: float) -> None:
        self.runner_data = RunnerData(runner_name, default_speed)

    def get_speed(self):
        return self.runner_data.default_speed

    def get_action_value(self):
        if math.isclose(self.runner_data.distance, 0.0):
            return 0.0
        speed = self.get_speed()
        return math.inf if math.isclose(speed, 0.0) else self.runner_data.distance / speed

    def action_advance(self, distance: float, status=Status.ADVANCED):
        self.runner_data.distance -= distance
        if self.runner_data.distance < 0:
            self.runner_data.distance = 0.0
        self.runner_data.status = status

    def action_delay(self, distance: float, status=Status.DELAYED):
        self.runner_data.distance += distance
        self.runner_data.status = status


class Schedule:
    def __init__(self, max_distance=10000.0, max_action_value_display=999) -> None:
        self.runners: list[Runner] = []
        self.max_distance = max_distance
        self.current_runner = None
        self.time = 0.0
        self.max_display = max_action_value_display

    def __str__(self) -> str:
        strings = []
        for runner in self.runners:
            if runner.runner_data.no_print:
                continue
            action_value = runner.get_action_value()
            if action_value > self.max_display:
                string = f"{runner.runner_data.name}({self.max_display})"
            else:
                string = f"{runner.runner_data.name}({action_value:.0f}"
            if runner.runner_data.previous_action_value > 0 and not math.isclose(action_value, runner.runner_data.previous_action_value):
                delta = action_value - runner.runner_data.previous_action_value
                if delta > self.max_display:
                    string += f"(+{self.max_display})"
                elif delta < -self.max_display:
                    string += f"(-{self.max_display})"
                else:
                    string += f"({delta:+.0f})"
            runner.runner_data.previous_action_value = action_value
            string += ")"
            strings.append(string)
        return "|".join(strings)

    def sort(self):
        self.runners.sort(key=lambda runner: (runner.get_action_value(), runner.runner_data.status))
        for runner in self.runners:
            runner.runner_data.status = Status.NORMAL

    def time_advance(self, time: float):
        for runner in self.runners:
            action_value = runner.get_action_value()
            runner.action_advance(time * runner.get_speed(), Status.NORMAL)
            runner.runner_data.previous_action_value -= action_value - runner.get_action_value()
        self.time += time

    def append(self, runner: Runner, reset_distance=True):
        self.runners.append(runner)
        if reset_distance:
            runner.runner_data.distance = self.max_distance

    def remove(self, runner: Runner):
        self.runners.remove(runner)

    def turn_out(self):
        if self.current_runner is not None and self.current_runner in self.runners:
            self.current_runner.runner_data.distance = self.max_distance
            self.current_runner.runner_data.status = Status.TURN_END
            self.current_runner.runner_data.previous_action_value = self.current_runner.get_action_value()
        self.sort()

    def turn_in(self):
        self.sort()
        self.current_runner = self.runners[0]
        time = self.current_runner.get_action_value()
        self.time_advance(time)
        return self.current_runner
