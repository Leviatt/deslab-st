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

The examples carry over the original plant, specifications, and PLC signal maps. The `actuators` argument maps event names to PLC signals, including sensor inputs, actuator outputs, and internal variables. `Mask` assigns outputs that mirror another PLC variable. `Isolated` contains a list of additional automata emitted alongside the supervisors and a list of event pairs used to emit direct signal logic. The optional `initial` event gates the generated program until its startup signal is active.

## Use an existing DESlab supervisor

Given a DESlab plant `G`, its synthesized supervisor `S`, and the event-to-signal dictionary `actuators`:

```python
from generator import process

project = process("ST_Generated")
project.register_automaton("supervisor", S, controllable=G.Sigcon)
project.load_automata(["supervisor"])
project.generate_ST_OPENPLC(["supervisor"], actuators=actuators, namest="controller")
```

Use the plant's controllable-event set when registering the supervisor. Supply a deterministic, reachable automaton with one initial state and no epsilon transitions. Use the DESlab event names as keys in the signal map. The existing emitter expects the signal conventions used in the examples, such as `GD_IN_0:ON:%IX0.0`, `GD_OUT_0:ON:%QX0.0`, and `INTERN_0:ON`.

## Verify against TCT

```powershell
python verify_st.py --legacy-repo 'D:\GitHub Repos\TCT_Proyext' --diff
```

The verifier runs both implementations in temporary directories. It skips legacy plotting and sorts shared-signal blocks in the temporary TCT emitter because the original used Python set iteration. The comparison uses exact ST text with line endings normalized. The reference is regenerated from the legacy scripts because the checked-in small-factory ST predates the current script. Running the examples requires only DESlab. Regenerating the reference also requires the original TCT environment.
