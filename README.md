# DESlab to OpenPLC

This project uses [DESlab](https://github.com/nebisman/deslab-py3) to compose plant and specification models and synthesize supervisors for the existing OpenPLC Structured Text generator.

## Generate the examples

From this directory with Python 3.11 or newer and Git installed:

```sh
python -m pip install -r requirements.txt
python Small_factory.py
python Assembly_line.py
python Transfer_line.py
```

Each script writes its `.st` file to `ST_Generated/`. Pass `--output-dir` to write elsewhere.

The examples carry over the original plant, specifications, and PLC signal maps.

## Use an existing DESlab supervisor

This two-state supervisor starts a motor from idle and returns to idle when a sensor reports completion.

```python
from deslab import fsa
from generator import process

G = fsa(
    ["idle", "running"],
    ["start_motor", "finished"],
    [("idle", "start_motor", "running"), ("running", "finished", "idle")],
    ["idle"],
    ["idle"],
    Sigcon=["start_motor"],
)
actuators = {
    "start_motor": "Motor:ON:%QX0.0",
    "finished": "RE_Finished:Sensor:%IX0.0",
}

project = process("ST_Generated")
project.register_automaton("supervisor", G, controllable=G.Sigcon)
project.load_automata(["supervisor"])
project.generate_ST_OPENPLC(["supervisor"], actuators=actuators, namest="controller")
```

If you synthesize a supervisor separately, register that automaton and pass the original plant's `Sigcon`. Each imported model must be deterministic and reachable with one initial state and no epsilon transitions. Its initial state becomes ST state 0.

For a model with no controllable events, pass `controllable=[]` explicitly. The pinned DESlab version can interpret `Sigcon=[]` in the `fsa` constructor as all events controllable.

| Argument | Meaning |
| --- | --- |
| `supervisors` | Names of the loaded supervisor automata, in the order used to emit and evaluate them. |
| `plants` | Registered plant names in supervisor order. Required when passing multiple supervisors. |
| `actuators` | Event-to-signal mapping for supervisors, auxiliary automata, and startup events. |
| `Mask` | Mapping from a source PLC variable to a list of `(mirror_variable, address)` pairs. |
| `Isolated` | A two-item list `[automaton_names, event_pairs]`. The loaded auxiliary automata get their own ST state variables. Each `(trigger_event, output_event)` pair adds direct signal logic. See `Small_factory.py` for an example. |
| `initial` | A mapped event whose signal enables the controller. The default `"null"` starts processing immediately. |

Map each event to one of these signal forms.

- `Motor:ON:%QX0.0` or `Motor:OFF:%QX0.0` for the two levels of a physical output. The same level form works for physical inputs. An alias such as `Motor:OFF` can omit the address after an earlier entry declares `Motor`.
- `RE_Finished:Sensor:%IX0.0` for a rising-edge input. Use an `FE` trigger name for a falling edge.
- `INTERN_0:ON` for an internal Boolean variable.

## Verify against TCT

```powershell
python verify_st.py --legacy-repo 'D:\GitHub Repos\TCT_Proyext' --diff
```

The verifier runs both implementations in temporary directories. It skips legacy plotting and sorts shared-signal blocks in the temporary TCT emitter because the original used Python set iteration. The comparison uses exact ST text with line endings normalized. The reference is regenerated from the legacy scripts because the checked-in small-factory ST predates the current script. Running the examples requires only DESlab. Regenerating the reference also requires the original TCT environment.

The generated program targets OpenPLC with a 20 ms task and an OpenPLC-specific random-number function block. Multi-supervisor generation checks conflicts pairwise. Validation of a new configuration should include global nonblocking analysis when applicable and compilation and execution in OpenPLC.
