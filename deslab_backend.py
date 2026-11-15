"""DESlab graph operations for OpenPLC supervisor coordination."""

from collections import deque

from deslab import allevents, fsa, parallel, product, supcontrollable
from deslab.src.algorithms import dfs


class DeslabBackend:
    """In-memory modeling and synthesis for the ST generation process."""

    def _coordinator(self, supervisors, plants, name):
        first, second = supervisors
        combined = parallel(self.models[first], self.models[second])
        if self._all_states_can_reach_marker(combined):
            return None

        controlled = self.controllable[first] | self.controllable[second]
        if combined.Sigcon != controlled:
            combined = combined.setpar(Sigcon=controlled)
        plant = parallel(*(self.models[plant] for plant in plants))
        required = parallel(combined, allevents(plant))
        supervisor = supcontrollable(required, combined)
        controlled |= required.Sigcon - combined.Sigma
        self.models[name] = self._reduce_supervisor(combined, supervisor, controlled)
        self.controllable[name] = controlled
        self._prepare_emission(name)
        return name

    @staticmethod
    def _all_states_can_reach_marker(model):
        # Parallel composition constructs only reachable states.
        return dfs(model.Graph.reverse(copy=False), model.Xm) == model.X

    def _reduce_supervisor(self, plant, supervisor, controlled):
        """Build a deterministic control congruence relative to the given plant."""
        self._require_deterministic("Coordinator", supervisor)
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
        return fsa(range(len(numbering)), supervisor.Sigma, transitions, [0], marked,
                   Sigcon=controlled & supervisor.Sigma)

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
