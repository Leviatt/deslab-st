"""Native DESlab component definitions and reference ordering for the examples."""

from deslab import fsa, supcontrollable


def synthesize(plant, specification, name, state_order_sources):
    """Synthesize with DESlab and retain pre-synthesis numbering for the ST comparison."""
    required = plant // specification
    supervisor = supcontrollable(required, plant)
    controllable = plant.Sigcon | (specification.Sigcon - plant.Sigma)
    supervisor = supervisor.setpar(name=name, Sigcon=supervisor.Sigma & controllable)
    state_order_sources[id(supervisor)] = required
    return supervisor


class ExampleComponents:
    """Retain declaration order for reproducing the legacy example output."""

    def __init__(self):
        self._events = {}
        self._transitions = {}

    @property
    def event_order(self):
        # TCT assigned consecutive odd and even codes to controllable and
        # uncontrollable events respectively, in declaration order.
        codes = {}
        next_code = {False: 0, True: 1}
        for event, controllable in self._events.items():
            codes[event] = next_code[controllable]
            next_code[controllable] += 2
        return sorted(codes, key=codes.__getitem__)

    def component(self, name, state_count, marked, transitions, *, uncontrollable=()):
        events = {event for _, event, _ in transitions}
        uncontrollable = set(uncontrollable)
        for _, event, _ in transitions:
            self._events.setdefault(event, event not in uncontrollable)
        controllable = {event for event in events if self._events[event]}
        model = fsa(range(state_count), events, transitions, [0], marked, name=name)
        model = model.setpar(Sigcon=controllable)
        self._transitions[model] = tuple((state, event) for state, event, _ in transitions)
        return model

    def allow(self, model, *events):
        """Add self-loops where these events have no transition."""
        return self._add_loops(model, events)

    def complete_spec(self, model):
        """Add missing uncontrollable self-loops to a specification."""
        events = [event for event in self._events if event in model.Sigma - model.Sigcon]
        return self._add_loops(model, events)

    def _add_loops(self, model, events):
        original = model
        transitions = list(self._transitions.pop(model))
        for event in events:
            for state in sorted(model.X):
                if event not in model.Gamma(state):
                    transitions.append((state, event))
                    model = model.addtransition((state, event, state))
        if model is not original:
            model = model.setpar(Sigcon={event for event in model.Sigma if self._events[event]})
        self._transitions[model] = tuple(transitions)
        return model

    def transition_order(self, models):
        return {id(model): self._transitions[model] for model in models if model in self._transitions}
