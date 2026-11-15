# DESlab to OpenPLC

This is the DESlab-based successor to [TCT_Proyect](https://github.com/Leviatt/TCT_Proyect). It produces equivalent OpenPLC Structured Text for the small factory, assembly line, and transfer line examples. The updated conflict check reduces generation time for the assembly line by skipping unnecessary automaton construction.

Use [DESlab](https://github.com/nebisman/deslab-py3) to define and visualize discrete-event automata, compose plant and specification models, synthesize supervisors, and check for conflicts between supervisor pairs. The generator turns those supervisors and their PLC signal maps into Structured Text (ST).

## Installation

Install Python 3.11 or newer and Git, then clone the project and install its dependencies.

```sh
git clone https://github.com/Leviatt/deslab-st.git
cd deslab-st
python -m pip install -r requirements.txt
```

Install the Graphviz system package and put `dot` on your PATH if you want to render automaton diagrams with Graphviz.

## Generate the examples

```sh
python Small_factory.py
python Assembly_line.py
python Transfer_line.py
```

Each script writes its `.st` file to `ST_Generated/`. Pass `--output-dir` to write elsewhere.

The examples carry over the original plant, specifications, and PLC signal maps.

## Model, synthesize, and generate ST

This two-state supervisor starts a motor from idle and returns to idle when a sensor reports completion.

```python
from deslab import fsa, parallel, supcontrollable
from generator import generate_ST_OPENPLC

G = fsa(
    ["idle", "running"],
    ["start_motor", "finished"],
    [("idle", "start_motor", "running"), ("running", "finished", "idle")],
    ["idle"],
    ["idle"],
    Sigcon=["start_motor"],
)
# B models the requirement that the motor finish before it can start again.
B = fsa(
    [0, 1],
    ["start_motor", "finished"],
    [(0, "start_motor", 1), (1, "finished", 0)],
    [0],
    [0],
    Sigcon=["start_motor"],
)
H = parallel(G, B)
S = supcontrollable(H, G)

actuators = {
    "start_motor": "Motor:ON:%QX0.0",
    "finished": "RE_Finished:Sensor:%IX0.0",
}

generate_ST_OPENPLC([S], plants=[G], actuators=actuators, namest="controller")
```

An `fsa` defines states, events, transitions as `(source, event, destination)` triples, initial states, marked states, and controllable events. Use `parallel` to compose components or synchronize the plant with a specification. Use `supcontrollable(specification, plant)` to synthesize the supervisor.

Pass DESlab automata directly to `generate_ST_OPENPLC`. The function reads the enabled events and transitions from the models already in memory. Each model must be deterministic and reachable with one initial state and no epsilon transitions. Its initial state becomes ST state 0.

When a plant is provided, it determines controllability for events in its alphabet. For a single supervisor with correct controllability already set, the call can be as short as `generate_ST_OPENPLC([S], actuators=actuators, namest="controller")`.

For a model with no controllable events, set `model = model.setpar(Sigcon=[])`. The pinned DESlab version can interpret `Sigcon=[]` in the `fsa` constructor as all events controllable.

### Visualize automata

In a notebook, pass the plant, specification, and supervisor to DESlab's drawing function.

```python
from deslab import draw

draw(G, H, S)
```

### Configure code generation

| Argument | Meaning |
| --- | --- |
| `supervisors` | DESlab supervisor automata, in the order used to emit and evaluate them. |
| `plants` | DESlab plant automata in supervisor order. Required when passing multiple supervisors. |
| `actuators` | Event-to-signal mapping for supervisors, auxiliary automata, and startup events. |
| `Mask` | Mapping from a source PLC variable to a list of `(mirror_variable, address)` pairs. |
| `Isolated` | A two-item list `[automata, event_pairs]`. The auxiliary DESlab automata get their own ST state variables. Each `(trigger_event, output_event)` pair adds direct signal logic. See `Small_factory.py` for an example. |
| `initial` | A mapped event whose signal enables the controller. The default `"null"` starts processing immediately. |
| `namest`, `output_dir` | Output filename stem and destination directory. The function also returns the ST source as a string. |
| `event_order` | Optional event priority order for generated branches. Events without an explicit priority are ordered by name. |

Map each event to one of these signal forms.

- `Motor:ON:%QX0.0` or `Motor:OFF:%QX0.0` for the two levels of a physical output. The same level form works for physical inputs. An alias such as `Motor:OFF` can omit the address after an earlier entry declares `Motor`.
- `RE_Finished:Sensor:%IX0.0` for a rising-edge input. Use an `FE` trigger name for a falling edge.
- `INTERN_0:ON` for an internal Boolean variable.

The generated program targets OpenPLC with a 20 ms task and an OpenPLC-specific random-number function block. Multi-supervisor generation checks conflicts pairwise. Validation of a new configuration should include global nonblocking analysis when applicable and compilation and execution in OpenPLC.

## Repository layout

- [`generator.py`](generator.py) emits OpenPLC Structured Text from in-memory DESlab models.
- [`deslab_backend.py`](deslab_backend.py) handles the graph operations used for supervisor coordination.
- [`Small_factory.py`](Small_factory.py), [`Assembly_line.py`](Assembly_line.py), and [`Transfer_line.py`](Transfer_line.py) define the three examples and their PLC signal maps.
- `ST_Generated/` is the default local output directory.

## Contributing

Open an issue for questions or bugs, or submit a pull request describing the change and how you tested it.
