"""Generate OpenPLC Structured Text from DESlab models."""

from pathlib import Path

from deslab_backend import DeslabBackend


class _STEmitter(DeslabBackend):
    """Emit directly from DESlab models using only ST state numbering."""

    def __init__(self, output_dir, event_order, state_order_sources, transition_order):
        self.output_dir = Path(output_dir)
        self.models = {}
        self.source_order = state_order_sources or {}
        self.transition_order = transition_order or {}
        self.dict_events = {event: index for index, event in enumerate(event_order or ())}
        self.controllable = {}
        self.numbering = {}
        self.event_lists = {}

    def _prepare_emission(self, name):
        model = self.models[name]
        self._require_deterministic(name, model)
        source = self.source_order.get(id(model), model)
        if id(model) in self.transition_order:
            ordered = sorted(model.X)
        elif hasattr(source, "Gamma"):
            ordered = [state for state in self._breadth_first_states(source) if state in model.X]
        else:
            ordered = list(source)
        if set(ordered) != model.X or len(ordered) != len(model.X):
            raise ValueError(f"{name!r} must have a complete ordering of reachable states")
        if ordered[0] not in model.X0:
            raise ValueError(f"{name!r} must start at ST state 0")
        self.numbering[name] = {state: index for index, state in enumerate(ordered)}
        enabled = dict.fromkeys(event for _, event, _, _ in self._transitions(name))
        controlled = self.controllable.get(name, model.Sigcon)
        self.event_lists[name] = (
            [event for event in enabled if event in controlled],
            [event for event in enabled if event not in controlled],
        )

    def _events(self, name):
        return self.event_lists[name]

    def _transitions(self, name):
        model = self.models[name]
        numbering = self.numbering[name]
        controlled = self.controllable.get(name, model.Sigcon)
        declaration = self.transition_order.get(id(model))
        if declaration is None:
            order = ((state, event) for state in numbering for event in self._ordered_events(model, state))
        else:
            order = declaration
        for state, event in order:
            yield numbering[state], event, numbering[model.delta(state, event)], event in controlled

    def _states(self, name):
        model = self.models[name]
        declaration = self.transition_order.get(id(model))
        if declaration is None:
            for state, index in self.numbering[name].items():
                yield index, self._ordered_events(model, state)
        else:
            events = {state: [] for state in self.numbering[name]}
            for state, event in declaration:
                events[state].append(event)
            for state, index in self.numbering[name].items():
                yield index, events[state]

    def aislated(self, aislated: list = [], actuators: list = [], interseccion=dict([])):
        # Generate ST code from Ailated supervisor and actuators.
        out = ""
        for a in aislated:
            add = ""
            if len(actuators[a[0]].split(':')) > 1:
                add = "NOT " if actuators[a[0]].split(':')[1] == 'OFF' else ''
            out += "\tIF NOT " + actuators[a[1]].split(':')[0] + " & " + add + actuators[a[0]].split(':')[
                0] + " THEN\n\t\t"
            out += actuators[a[1]].split(':')[0] + " := 1;\n"
            out += "\tELSIF " + actuators[a[1]].split(':')[0] + " & " + add + actuators[a[0]].split(':')[
                0] + " THEN\n\t\t"
            out += actuators[a[0]].split(':')[0] + " := 0;\n\t"
            if actuators[a[0]].split(':')[0] in interseccion.keys():
                out += "\t" + actuators[a[0]].split(':')[0] + "_G[0] := 0;\n"
            out += "END_IF;\n"
        return out


    def generate_ST_OPENPLC(self, supervisors: list, plants: list = [], actuators: dict = dict([]), namest='code_st',
                            Mask: dict = dict([]), Isolated: list = [], initial: str = "null"):
        # Generate the full ST code
        if not supervisors:
            raise ValueError("At least one supervisor is required")
        if len(supervisors) > 1 and len(plants) != len(supervisors):
            raise ValueError("Supply one plant per supervisor, in the same order")
        if Isolated and len(Isolated) != 2:
            raise ValueError("Isolated must contain [automaton_names, event_pairs]")
        names = [*supervisors, *(Isolated[0] if Isolated else [])]
        required = set()
        for name in names:
            controlled, uncontrolled = self._events(name)
            required.update(controlled)
            required.update(uncontrolled)
        for first, second in Isolated[1] if Isolated else ():
            required.update((first, second))
        if initial != "null":
            required.add(initial)
        missing = required.difference(actuators)
        if missing:
            raise ValueError("Missing PLC signal mappings for: " + ", ".join(sorted(map(str, missing))))
        signals = set()
        for event, mapping in actuators.items():
            fields = mapping.split(":") if isinstance(mapping, str) else []
            if (len(fields) == 2 and all(fields) and fields[1] in ("ON", "OFF")
                    and ("INTERN" in fields[0] or fields[0] in signals)):
                continue
            if len(fields) == 3 and all(fields):
                if fields[1] in ("ON", "OFF"):
                    signals.add(fields[0])
                    continue
                if fields[0].startswith(("RE", "FE")):
                    signals.add(fields[1])
                    continue
            raise ValueError(f"Invalid PLC mapping for {event!r}: {mapping!r}")

        RANDOM = "FUNCTION_BLOCK random_number\n\tVAR_INPUT\n\t\tIN : BOOL;\n\tEND_VAR\n\tVAR\n\t\tM : BOOL;"
        RANDOM += "\n\t\tINIT : BOOL;\n\tEND_VAR\n\tVAR_OUTPUT\n\t\tOUT : DINT;\n\tEND_VAR\n"
        RANDOM += "\n\tIF INIT = 0 THEN\n\t\t{#include <stdio.h>}\n\t\t{#include <stdlib.h>}\n\t\tIN := 1;\n\tEND_IF;"
        RANDOM += "\n\tIF M = 0 and IN = 1 THEN\n\t\t{SetFbVar(OUT,rand())}\n\tEND_IF;\nEND_FUNCTION_BLOCK\n"
        HEADER = "PROGRAM tesis0\n"
        END = "\nEND_PROGRAM\n\n"
        END += "CONFIGURATION Config0\n\n\tRESOURCE Res0 ON PLC\n\t\tTASK task0(INTERVAL := T#20ms,PRIORITY := 0);"
        END += "\n\t\tPROGRAM instance0 WITH task0 : tesis0;" + "\n\tEND_RESOURCE\nEND_CONFIGURATION"

        intersections = {}
        coordinators = []
        for i, first in enumerate(supervisors):
            for j in range(i + 1, len(supervisors)):
                second = supervisors[j]
                coordinator = self._coordinator((first, second), (plants[i], plants[j]), f"CO_{i}_{j}")
                if coordinator is not None:
                    coordinators.append((coordinator, i, j))
                shared = set(self._events(first)[0]) & set(self._events(second)[0])
                for signal in sorted({actuators[event].split(":")[0] for event in shared}):
                    participants = intersections.setdefault(signal, [])
                    for index in (i, j):
                        if index not in participants:
                            participants.append(index)

        for coordinator, i, j in coordinators:
            for event in self._events(coordinator)[0]:
                signal = actuators[event].split(":")[0]
                if signal not in intersections:
                    intersections[signal] = [
                        index for index in (i, j) if event in self._events(supervisors[index])[0]
                    ]

        auxiliary, event_pairs = Isolated or ((), ())
        controlled = []
        uncontrolled = []
        cases = []
        selections = []
        main_models = supervisors if actuators or len(supervisors) == 1 else []
        for index, model in enumerate([*main_models, *auxiliary]):
            guards_on, guards_off = self.ifs(model, actuators, index)
            shared = intersections if index < len(main_models) else {}
            case, selection_count = self.sw_case(model, actuators, index, shared)
            controlled.append(guards_on + "\n")
            uncontrolled.append(guards_off + "\n")
            cases.append("\n" + case + "\n")
            selections.append(selection_count)

        coordinator_cases = []
        coordinator_on = []
        coordinator_off = []
        coordinator_names = [name for name, _, _ in coordinators]
        for name in coordinator_names:
            index = len(selections)
            coordinator_cases.append(self.coordinator_sc(name, state_it=index, actuators=actuators))
            guards_on, guards_off = self.ifs(name, actuators, index)
            coordinator_on.append(guards_on)
            coordinator_off.append(guards_off)
            selections.append(0)

        coordinated_signals = {
            actuators[event].split(":")[0]
            for name in coordinator_names for event in self._events(name)[0]
        }
        declaration = self.declaration_OPENPLC(
            actuators, selections, intersections, coordinator_names, Mask, initial,
        )
        mask = "".join(
            f"\t{output} := {signal};\n " for signal, mirrors in Mask.items() for output, _ in mirrors
        )
        body = "".join([
            *uncontrolled, *coordinator_off, *cases, *coordinator_cases,
            self.intersection(intersections, coordinated_signals), *coordinator_on, *controlled,
            self.aislated(event_pairs, actuators, intersections), mask,
        ])
        if initial != "null":
            startup_signal = actuators[initial].split(":")[0]
            indented_body = "\n".join("\t" + line for line in body.splitlines())
            body = (
                f"\tIF NOT initial THEN\n\t\tIF {startup_signal} THEN\n"
                "\t\t\tinitial := 1;\n\t\tEND_IF;\n\tELSIF initial THEN\n"
                + indented_body + "\n\tEND_IF;"
            )
        out = RANDOM + HEADER + declaration + body + END
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / f"{namest}.st").write_text(out, encoding="utf-8", newline="\n")
        return out

    def intersection(self, intersection: dict, coordinated_signals=(), addG="_G[", addC="_C[", name_intersection="aux"):
        # Generate the code for the intersection between supervisors and coordinators
        out = ""
        for inter in intersection.keys():
            coordinated = inter in coordinated_signals
            aux = ""
            coor = ""
            bandera = name_intersection if coordinated else inter
            guesses = []
            for act in range(len(intersection[inter])):
                guesses.append(inter + addG + str(act) + "]")

            if len(guesses) != 1:
                if len(guesses) == 2:
                    out += "\tIF "
                    out += guesses[0] + " <> " + guesses[1] + " THEN\n"
                    out += "\t\t" + guesses[0] + " := " + inter + ";\n"
                    out += "\t\t" + guesses[1] + " := " + inter + ";"
                else:
                    out += "\tIF "
                    i = 0
                    j = 1
                    while j < len(guesses):
                        aux += "\t\t" + guesses[i] + " := " + inter + ";\n"
                        out += "(" + guesses[i] + " <> " + guesses[j] + ")"
                        i += 1
                        j += 1
                        if j != len(guesses):
                            out += " OR "
                        else:
                            out += " THEN\n"
                    aux += "\t\t" + guesses[j - 1] + " := " + inter + ";\t\t\t"
            if coordinated:
                coor += "\tIF " + bandera + " XOR " + inter + " THEN\n\t\t"
                coor += "IF NOT " + bandera + " & " + inter + addC + "0] THEN\n\t\t\t"
                coor += inter + " := 0;\n\t\t"
                coor += "ELSIF " + bandera + " & " + inter + addC + "1] THEN\n\t\t\t"
                coor += inter + " := 1;"
                coor += "\n\t\tEND_IF;"
                coor += "\n\tEND_IF;\n"
                coor += "\t" + inter + addG + "0] := " + inter + ";\n"
            out += aux + '\n'
            if len(guesses) != 1:
                out += "\tEND_IF;\n"

            out += "\t" + bandera + " := " + guesses[0] + ";\n"
            out += coor
        return out


    def declaration_OPENPLC(self, actuators, n_state, intersetion, CO, mascara, initial):
        # Variable blocks for OPENPLC ST version

        declaration = "\tVAR\n"
        clocks = ""
        start = "\tVAR\n"
        start += '\t\trandom : random_number;\n'
        start += '\t\trandom_num : DINT;\n'
        if initial != 'null':
            start += '\t\tinitial : BOOL;\n'
        start += f"\t\tstate : ARRAY [0..{len(n_state)}] OF DINT;\n"
        if len(CO) != 0:
            declared = []
            start += "\t\taux : BOOL := 0;\n"
            for coor in CO:
                for i in self._events(coor)[0]:
                    aux = actuators[i].split(':')[0]
                    if aux not in declared:
                        start += "\t\t" + aux + "_C : ARRAY [0..1] OF BOOL;\n"
                        declared.append(aux)
        for index, count in enumerate(n_state):
            if count:
                start += f"\t\tslt{index} : ARRAY [0..{count}] OF DINT;\n"

        if len(intersetion.keys()) > 0:
            for inter in intersetion.keys():
                start += "\t\t" + inter + "_G : ARRAY [0.." + str(len(intersetion[inter])) + "] OF BOOL;\n"

        declared = []
        for msk in mascara.keys():
            for e in mascara[msk]:
                declaration += "\t\t" + e[0] + " AT " + e[1] + " : BOOL;\n "
        for act in actuators.values():
            aux = act.split(':')
            if 'INTERN' in aux[0]:
                if aux[0] not in declared:
                    start += "\t\t" + aux[0] + " : BOOL;\n"
                    declared.append(aux[0])
                    continue
            if aux[1] == 'ON' or aux[1] == 'OFF':
                if aux[0] in declared:
                    continue
                declaration += "\t\t" + aux[0] + " AT " + aux[2] + " : BOOL;\n"
                declared.append(aux[0])
            else:
                if aux[1] not in declared:
                    declared.append(aux[1])
                    declaration += "\t\t" + aux[1] + " AT " + aux[2] + " : BOOL;\n"
                start += "\t\t" + aux[0] + " : "

                if aux[0].startswith("FE"):
                    start += "F_TRIG;\n"
                if aux[0].startswith("RE"):
                    start += "R_TRIG;\n"

                clocks += "\t" + aux[0] + '(CLK:= ' + aux[1] + ');\n'
        ran = "\trandom(\n\t\tIN := True,\n\t\tOUT => random_num);\n"
        start += "\tEND_VAR\n"
        declaration += "\tEND_VAR\n"
        return start + declaration + clocks + ran


    def ifs(self, name: str, actuators=dict([]), n_state=0):  # Generate the ST code for conditional sentences
        if_uncontrollable = "\t"
        if_controllable = "\t"
        for origin, event, destination, controllable in self._transitions(name):
            if origin == destination:
                continue
            name_event = actuators.get(event, event)
            name_event = name_event.split(':')
            edge_trigger = name_event[1] not in ("ON", "OFF")

            if name_event[1] == 'OFF':
                name_event = 'NOT ' + name_event[0]
            else:
                name_event = name_event[0]
            if controllable:
                if_controllable += "IF state[" + str(n_state) + "] = " + str(origin) \
                                   + " & " + name_event \
                                   + " THEN\n  " + "\t\t" + "state[" + str(n_state) + "] := " \
                                   + str(destination) + ";\n  " + "\tELS"
            else:
                if_uncontrollable += "IF state[" + str(n_state) + "] = " + str(origin) + " & "
                if_uncontrollable += name_event + ('.Q' if edge_trigger else '')
                if_uncontrollable += " THEN\n  " + "\t\t" + "state[" + str(n_state) + "] := "
                if_uncontrollable += str(destination) + ";\n  " + "\tELS"
        if if_controllable == "\t": if_controllable = ""
        if if_uncontrollable == "\t": if_uncontrollable = ""
        if not if_controllable == "":
            if_controllable = if_controllable.rstrip("ELS") + "END_IF;\n"
        if not if_uncontrollable == "":
            if_uncontrollable = if_uncontrollable.rstrip("ELS") + "END_IF;\n"
        return if_controllable, if_uncontrollable


    def sw_case(self, name, actuators, state_index, intersections):
        guesses = {
            signal: f"_G[{participants.index(state_index)}]"
            for signal, participants in intersections.items() if state_index in participants
        }
        outputs = {}
        for event in self._events(name)[0]:
            signal, level, *_ = actuators[event].split(":")
            value = int(level != "OFF")
            outputs[event] = (f"{signal}{guesses.get(signal, '')} := {value};", value)

        selections = 0
        case = f"\tCASE state[{state_index}] OF\n  "
        for state, active_events in self._states(name):
            assignments = [outputs[event] for event in active_events if event in outputs]
            if not assignments:
                continue
            case += f"\t\t{state}:\n  "
            if len(assignments) == 1:
                assignment, value = assignments[0]
                case += f"\t\t\t{assignment}\n"
                if value == 0:
                    case += "  "
                continue
            selector = f"slt{state_index}[{selections}]"
            case += f"\t\t\tCASE {selector} OF\n  "
            for option, (assignment, _) in enumerate(assignments):
                case += f"\t\t\t\t{option}:\n  \t\t\t\t\t{assignment}\n  "
            case += (
                "\t\t\tEND_CASE;\n  "
                f"\t\t\t{selector} := (random_num + {selector}) MOD {len(assignments)};\n  "
                f"\t\t\trandom_num := random_num - {selector};\n "
            )
            selections += 1
        return case + "\tEND_CASE;", selections

    def coordinator_sc(self, name, state_it, actuators):
        flags = {}
        for event in self._events(name)[0]:
            signal, level, *_ = actuators[event].split(":")
            flags[event] = f"{signal}_C[{int(level != 'OFF')}]"

        case = f"\tCASE state[{state_it}] OF\n  "
        if flags:
            for state, active_events in self._states(name):
                enabled = set(active_events)
                case += f"\t\t{state}:\n  "
                for event, flag in flags.items():
                    case += f"\t\t\t{flag} := {int(event in enabled)};\n"
        return case + "\tEND_CASE;\n  "


def generate_ST_OPENPLC(supervisors, plants=(), actuators=None, namest="controller",
                        Mask=None, Isolated=None, initial="null", *,
                        output_dir="ST_Generated", event_order=None):
    """Generate and save OpenPLC ST from in-memory DESlab automata.

    Supply one plant per supervisor when using multiple supervisors.
    Isolated contains auxiliary automata followed by pairs of mapped events.
    """
    return _generate_st(supervisors, plants, actuators, namest, Mask, Isolated, initial,
                        output_dir=output_dir, event_order=event_order)


def _generate_st(supervisors, plants, actuators, namest, Mask, Isolated, initial, *,
                 output_dir, event_order, state_order_sources=None, transition_order=None):
    supervisors = tuple(supervisors)
    plants = tuple(plants)
    if (plants or len(supervisors) > 1) and len(plants) != len(supervisors):
        raise ValueError("Supply one plant per supervisor, in the same order")
    if Isolated and len(Isolated) != 2:
        raise ValueError("Isolated must contain [automata, event_pairs]")
    emitter = _STEmitter(output_dir, event_order, state_order_sources, transition_order)
    supervisor_names = []
    plant_names = []
    for index, supervisor in enumerate(supervisors):
        emitter._require_deterministic(f"Supervisor {index}", supervisor)
        name = f"supervisor_{index}"
        emitter.models[name] = supervisor
        if plants:
            plant = plants[index]
            emitter._require_deterministic(f"Plant {index}", plant)
            plant_name = f"plant_{index}"
            emitter.models[plant_name] = plant
            plant_names.append(plant_name)
            emitter.controllable[name] = (plant.Sigcon & supervisor.Sigma) | (supervisor.Sigcon - plant.Sigma)
        else:
            emitter.controllable[name] = supervisor.Sigcon
        emitter._prepare_emission(name)
        supervisor_names.append(name)
    isolated = []
    if Isolated:
        isolated_names = []
        for index, model in enumerate(Isolated[0]):
            name = f"isolated_{index}"
            emitter.models[name] = model
            emitter._prepare_emission(name)
            isolated_names.append(name)
        isolated = [isolated_names, Isolated[1]]
    return emitter.generate_ST_OPENPLC(supervisor_names, plant_names, actuators or {}, namest,
                                       Mask or {}, isolated, initial)
