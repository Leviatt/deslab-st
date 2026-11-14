"""Compile DESlab automata into the inputs consumed by the ST emitter."""

from collections import deque
from functools import reduce

from deslab import allevents, fsa, parallel, product, supcontrollable
from deslab.src.algorithms import dfs


class DeslabBackend:
    """In-memory modeling and synthesis for the ST generation process."""

    def register_automaton(self, name, model, *, controllable=None):
        """Register a native DESlab model.

        When importing a supervisor, pass its plant's Sigcon as
        controllable so the PLC uses the plant's event classifications.
        """
        events = model.Sigcon if controllable is None else controllable
        self.models[name] = model.setpar(name=name, Sigcon=model.Sigma.intersection(events))
        self.state_order_sources.pop(name, None)
        return name

    def generate_automata(self, name):
        """Build a DESlab model from a legacy component declaration."""
        automaton = self.automatas[name]
        events = set(automaton.c_events) | set(automaton.uc_events)
        transitions = [
            (src, self.dict_events_name[str(event_id)], dst)
            for src, event_id, dst in automaton.transitions
        ]
        marked = [automaton.dict_states[state] for state in automaton.states_marked]
        controllable = set(automaton.c_events)
        model = fsa(range(len(automaton.states)), events, transitions, [0], marked)
        return self.register_automaton(name, model, controllable=controllable)

    def generate_all_automata(self):
        for name in self.automatas:
            self.generate_automata(name)

    def automata_syncronize(self, automata_names, name_sync=""):
        models = (self.models[name] for name in automata_names)
        return self.register_automaton(name_sync, reduce(parallel, models))

    def all_events(self, automata_name, alleventsname):
        source = self.models[automata_name]
        return self.register_automaton(
            alleventsname, allevents(source), controllable=source.Sigcon
        )

    def supcon(self, plant, specifications, sup=""):
        source = self.models[plant]
        specification = self.models[specifications]
        required = parallel(source, specification)
        # Composition retains specification-only events. The legacy event
        # table assigned them globally before constructing the models.
        controllable = source.Sigcon | (specification.Sigcon - source.Sigma)
        supervisor = supcontrollable(required, source)
        self.register_automaton(sup, supervisor, controllable=controllable)
        self.state_order_sources[sup] = required
        return sup

    def nonconflict(self, first, second):
        combined = parallel(self.models[first], self.models[second])
        return self._all_states_can_reach_marker(combined)

    def coordinator(self, supervisors, plants):
        """Check a supervisor pair and prepare its synthesis inputs on conflict."""
        combined = self.automata_syncronize(supervisors, "SUPt")
        # The alphabet automaton has one marked state and a self-loop for
        # every event in its alphabet. It cannot change blocking behavior.
        if self._all_states_can_reach_marker(self.models[combined]):
            return True, combined, None
        plant = self.automata_syncronize(plants, "plantaTotal")
        alphabet = self.all_events(plant, "AEcoor")
        return False, combined, alphabet

    @staticmethod
    def _all_states_can_reach_marker(model):
        # Parallel composition constructs only reachable states.
        return dfs(model.Graph.reverse(copy=False), model.Xm) == model.X

    def reduce_supervisor(self, plant_name, supervisor_name, name):
        """Build a deterministic control congruence relative to the given plant."""
        plant = self.models[plant_name]
        supervisor = self.models[supervisor_name]
        self._require_deterministic(supervisor_name, supervisor)
        states = list(self._breadth_first_states(supervisor))
        disabled = {state: set() for state in states}
        plant_marked = set()
        for sup_state, plant_state in product(supervisor, plant).X:
            disabled[sup_state].update(plant.Gamma(plant_state) - supervisor.Gamma(sup_state))
            if plant_state in plant.Xm:
                plant_marked.add(sup_state)

        partition = {state: frozenset({state}) for state in states}
        for index, left in enumerate(states):
            for right in states[index + 1:]:
                if partition[left] == partition[right]:
                    continue
                candidate = self._merge_control_cells(
                    partition, supervisor, disabled, plant_marked, left, right
                )
                if candidate is not None:
                    partition = candidate

        numbering = {
            cell: index for index, cell in enumerate(dict.fromkeys(partition.values()))
        }
        transitions = {
            (
                numbering[partition[state]],
                event,
                numbering[partition[supervisor.delta(state, event)]],
            )
            for state in states
            for event in supervisor.Gamma(state)
        }
        marked = {numbering[partition[state]] for state in supervisor.Xm}
        reduced = fsa(range(len(numbering)), supervisor.Sigma, transitions, [0], marked)
        return self.register_automaton(name, reduced, controllable=supervisor.Sigcon)

    @staticmethod
    def _merge_control_cells(partition, supervisor, disabled, plant_marked, left, right):
        candidate = partition.copy()
        pending = [(left, right)]
        while pending:
            left, right = pending.pop()
            left_cell, right_cell = candidate[left], candidate[right]
            if left_cell == right_cell:
                continue
            for first in left_cell:
                for second in right_cell:
                    if (
                        supervisor.Gamma(first) & disabled[second]
                        or supervisor.Gamma(second) & disabled[first]
                        or (
                            (first in plant_marked) == (second in plant_marked)
                            and (first in supervisor.Xm) != (second in supervisor.Xm)
                        )
                    ):
                        return None

            merged = left_cell | right_cell
            targets = {}
            for state in merged:
                candidate[state] = merged
                for event in supervisor.Gamma(state):
                    target = supervisor.delta(state, event)
                    previous = targets.setdefault(event, target)
                    if candidate[target] != candidate[previous]:
                        pending.append((target, previous))
        return candidate

    def load_automata(self, names):
        """Load registered DESlab models into the ST emitter's representation."""
        for name in names:
            model = self.models[name]
            self._require_deterministic(name, model)
            events = sorted(model.Sigma, key=str)
            for event in events:
                if event in self.dict_events:
                    is_controllable = int(self.dict_events[event]) % 2 == 1
                    if is_controllable != (event in model.Sigcon):
                        raise ValueError(f"Inconsistent controllability for {event!r} in {name!r}")
            for event in events:
                if event not in self.dict_events:
                    self._register_event(event, event in model.Sigcon)

            ordering_model = self.state_order_sources.get(name, model)
            ordered_states = (
                state for state in self._breadth_first_states(ordering_model)
                if state in model.X
            )
            states = {state: index for index, state in enumerate(ordered_states)}
            if len(states) != len(model.X):
                raise ValueError(f"{name!r} contains states unreachable from its initial state")

            transitions = []
            labels = []
            for state in states:
                for event in self._ordered_events(model, state):
                    target = model.delta(state, event)
                    transitions.append((states[state], states[target]))
                    labels.append(event)

            uncontrolled = [event for event in events if event not in model.Sigcon]
            self.new_automaton(name)
            self.add_state(name, len(states), [], [state in model.Xm for state in states])
            self.add_transition(name, transitions, labels, uncontrolled)

    @staticmethod
    def _require_deterministic(name, model):
        if model.empty or len(model.X0) != 1 or not model.is_dfa() or model.has_epsilon():
            raise ValueError(
                f"{name!r} must be a nonempty deterministic automaton without epsilon events"
            )

    def _ordered_events(self, model, state):
        def event_order(event):
            if event in self.dict_events:
                return (0, int(self.dict_events[event]))
            return (1, str(event))

        return sorted(model.Gamma(state), key=event_order)

    def _breadth_first_states(self, model):
        initial = next(iter(model.X0))
        pending = deque([initial])
        seen = {initial}
        while pending:
            state = pending.popleft()
            yield state
            for event in self._ordered_events(model, state):
                target = model.delta(state, event)
                if target not in seen:
                    seen.add(target)
                    pending.append(target)

    def _register_event(self, event, controllable):
        group = self.c_events if controllable else self.uc_events
        event_id = str(2 * len(group) + int(controllable))
        group.append(event)
        self.dict_events[event] = event_id
        self.dict_events_name[event_id] = event
