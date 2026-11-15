"""Generate OpenPLC Structured Text for the small factory with machine failures and repairs."""

from argparse import ArgumentParser
from pathlib import Path

from deslab import allevents

from example_models import ExampleComponents, synthesize
from generator import generate_ST_OPENPLC


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "ST_Generated"


def build(output_dir=DEFAULT_OUTPUT_DIR):
    actuators = dict([])
    actuators['M1_ON'] = 'GD_OUT_0:ON:%QX100.0'
    actuators['M1_OFF'] = 'GD_OUT_0:OFF'
    actuators['M2_ON'] = 'GD_OUT_1:ON:%QX100.1'
    actuators['M2_OFF'] = 'GD_OUT_1:OFF'
    actuators['M1_Bussy'] = 'GD_IN_0:ON:%IX100.0'
    actuators['M1_NOT_Bussy'] = 'GD_IN_0:OFF:%IX100.0'
    actuators['M2_Bussy'] = 'GD_IN_1:ON:%IX100.1'
    actuators['M1_END'] = 'FE_M1E:GD_IN_0:%IX100.0'  # 10
    actuators['M2_END'] = 'FE_M2E:GD_IN_1:%IX100.1'  # 20
    actuators['start'] = 'GD_IN_15:ON:%IX100.5'
    actuators['BA_ON'] = 'GD_OUT_2:ON:%QX100.2'
    actuators['BA_OFF'] = 'GD_OUT_2:OFF'
    actuators['Fed'] = 'FE_A:GD_IN_2:%IX100.2'
    actuators['Buffer_conveyor_ON'] = 'GD_OUT_4:ON:%QX100.4'
    actuators['Buffer_conveyor_ON_UC'] = 'GD_OUT_4:ON:%QX100.4'
    actuators['Buffer_conveyor_OFF'] = 'GD_OUT_4:OFF'
    actuators['Piece_located'] = 'FE_PL:GD_IN_3:%IX100.3'
    actuators['Piece_ready'] = 'FE_PR:GD_IN_4:%IX100.4'
    actuators['Piece_restart_ON'] = 'GD_OUT_5:ON:%QX100.5'
    actuators['Piece_restart_OFF'] = 'GD_OUT_5:OFF:%QX100.5'
    actuators['Blade_ON'] = 'GD_OUT_6:ON:%QX100.6'
    actuators['Blade_OFF'] = 'GD_OUT_6:OFF:%QX100.6'
    actuators['M1_BROKEN'] = 'GD_IN_10:OFF:%IX101.0'  # 12 %IX101.0 IX102.4 PIN17
    actuators['M2_BROKEN'] = 'GD_IN_11:OFF:%IX101.1'  # 22 %IX101.1 PIN23
    actuators['M1_REPAIR'] = 'GD_IN_12:ON:%IX101.2'  # %IX101.2 PIN18
    actuators['M2_REPAIR'] = 'GD_IN_13:ON:%IX101.3'  # %IX101.3 PIN19
    actuators['M1_REPAIR_DONE'] = 'INTERN_4:OFF'
    actuators['M2_REPAIR_DONE'] = 'INTERN_5:OFF'
    actuators['M1_REPAIR_OUT_ON'] = 'GD_OUT_10:ON:%QX101.2'
    actuators['M2_REPAIR_OUT_ON'] = 'GD_OUT_11:ON:%QX101.3'
    actuators['M1_REPAIR_OUT_OFF'] = 'GD_OUT_10:OFF:%QX101.2'
    actuators['M2_REPAIR_OUT_OFF'] = 'GD_OUT_11:OFF:%QX101.3'
    actuators['R1_PERMITTED'] = 'INTERN_2:ON'
    actuators['R2_PERMITTED'] = 'INTERN_3:ON'
    actuators['R1_NOT_PERMITTED'] = 'INTERN_2:OFF'
    actuators['R2_NOT_PERMITTED'] = 'INTERN_3:OFF'
    actuators['11'] = 'INTERN_0:ON'
    actuators['21'] = 'INTERN_1:ON'  # M1_arriving

    Mask = dict([])
    Mask['GD_OUT_2'] = [('GD_OUT_3', '%QX100.3')]  # BANDM1 -> EMITER
    Mask['NOT GD_IN_10'] = [('GD_OUT_8', '%QX101.0')]  # M1_BROKEN -> M1_BROKEN
    Mask['NOT GD_IN_11'] = [('GD_OUT_9', '%QX101.1')]  # M2_BROKEN -> M2_BROKEN
    components = ExampleComponents()
    state_order_sources = {}

    M1 = components.component(
        'M1', 4, [0, 1, 2, 3],
        [(0, 'M1_ON', 1), (1, 'M1_Bussy', 2), (2, 'M1_OFF', 3), (3, 'M1_END', 0)],
        uncontrollable=['M1_ON', 'M1_Bussy', 'M1_END'],
    )
    M1 = components.allow(M1, 'M1_ON', 'M1_Bussy', 'M1_END')

    Buffer_fill = components.component(
        'Buffer_fill', 10, range(10),
        [(0, 'start', 1), (1, 'M1_END', 2), (2, 'Buffer_conveyor_ON', 3), (3, 'Piece_ready', 4),
         (4, 'Buffer_conveyor_OFF', 5), (5, 'M2_END', 2), (7, 'M2_END', 2), (5, 'M1_END', 6),
         (6, 'Buffer_conveyor_ON', 7), (7, 'Piece_located', 8), (8, 'Buffer_conveyor_OFF', 5),
         (1, 'M1_BROKEN', 9), (9, 'M1_END', 1)],
        uncontrollable=['start', 'M1_END', 'M2_END', 'Piece_ready', 'Piece_located', 'M1_BROKEN'],
    )

    Blade = components.component(
        'Blade', 4, [],
        [(0, 'M2_END', 1), (1, 'Blade_OFF', 2), (2, 'Piece_ready', 3), (3, 'Blade_ON', 0)],
        uncontrollable=['M2_END', 'Piece_ready'],
    )

    generate = components.component(
        'generate', 6, [],
        [(0, 'M1_Bussy', 1), (1, 'M1_END', 2), (2, 'Piece_restart_ON', 3),
         (3, 'Piece_located', 4), (4, 'Piece_restart_OFF', 0), (1, 'M1_BROKEN', 5),
         (5, 'M1_END', 0)],
        uncontrollable=['Piece_located', 'M1_Bussy', 'M1_END', 'M1_BROKEN'],
    )

    M2 = components.component(
        'M2', 4, [0, 1, 2, 3],
        [(0, 'M2_ON', 1), (1, 'M2_Bussy', 2), (2, 'M2_OFF', 3), (3, 'M2_END', 0)],
        uncontrollable=['M2_ON', 'M2_Bussy', 'M2_END'],
    )

    B_A = components.component(
        'B_A', 4, [0, 1, 2, 3],
        [(0, 'BA_ON', 1), (1, 'Fed', 2), (2, 'BA_OFF', 3), (3, 'M1_END', 0)],
        uncontrollable=['Fed', 'M1_END'],
    )

    start = components.component(
        'start', 2, [0, 1],
        [(0, 'start', 1), (1, 'BA_ON', 1)],
        uncontrollable=['start'],
    )
    B_A = components.allow(B_A, 'start')
    start = components.complete_spec(start)

    model_M1 = components.component(
        'model_M1', 3, [0],
        [(0, '11', 1), (1, 'Piece_located', 0), (1, 'M1_BROKEN', 2), (2, 'M1_NOT_Bussy', 0)],
        uncontrollable=['Piece_located', 'M1_BROKEN', 'M1_NOT_Bussy'],
    )

    model_M2 = components.component(
        'model_M2', 3, [0],
        [(0, '21', 1), (1, 'M2_END', 0), (1, 'M2_BROKEN', 2), (2, 'M2_END', 0)],
        uncontrollable=['M2_END', 'M2_BROKEN'],
    )

    REQ_Buffer = components.component(
        'REQ_Buffer', 3, [0, 1, 2],
        [(0, 'Piece_located', 1), (1, '21', 0), (1, 'Piece_located', 2), (2, '21', 1)],
        uncontrollable=['Piece_located'],
    )

    REQ_repair = components.component(
        'REQ_repair', 2, [0, 1],
        [(0, 'M1_REPAIR_OUT_ON', 0), (0, 'M2_BROKEN', 1), (1, 'M2_REPAIR_OUT_ON', 0)],
        uncontrollable=['M2_BROKEN'],
    )

    REQ_repair = components.complete_spec(REQ_repair)

    REQ_start = components.component(
        'REQ_start', 2, [0, 1],
        [(0, 'start', 1), (1, '11', 1), (1, '21', 1)],
        uncontrollable=['start'],
    )
    model_M1 = components.allow(model_M1, 'start')

    REQ_start = components.complete_spec(REQ_start)

    # Ideal model have the repair action as a controllable event, but if it is controllable when the supervisor get a machine broken
    # It will repair the machine in the same cicle, therefore a new automaton called "repair" its created to work with an button
    # The button will repair the machine and start the event M1_REPAIR_OUT_ON

    repair = components.component(
        'repair', 20, range(20),
        [(0, 'M1_BROKEN', 1), (1, 'R1_PERMITTED', 2), (2, 'M1_REPAIR', 3),
         (3, 'M1_REPAIR_OUT_ON', 4), (4, 'R1_NOT_PERMITTED', 5), (5, 'M1_NOT_Bussy', 6),
         (6, 'M1_REPAIR_OUT_OFF', 0), (0, 'M2_BROKEN', 7), (7, 'R2_PERMITTED', 8),
         (8, 'M2_REPAIR', 9), (9, 'M2_REPAIR_OUT_ON', 10), (10, 'R2_NOT_PERMITTED', 11),
         (11, 'M2_END', 12), (12, 'M2_REPAIR_OUT_OFF', 0), (2, 'M2_BROKEN', 13),
         (13, 'R1_NOT_PERMITTED', 14), (14, 'R2_PERMITTED', 15), (15, 'M2_REPAIR', 16),
         (16, 'M2_REPAIR_OUT_ON', 17), (17, 'R2_NOT_PERMITTED', 18), (18, 'M2_END', 19),
         (19, 'M2_REPAIR_OUT_OFF', 1), (8, 'M1_BROKEN', 15)],
        uncontrollable=['M1_BROKEN', 'M2_BROKEN', 'M1_REPAIR', 'M2_REPAIR', 'M1_NOT_Bussy', 'M2_END'],
    )

    plant_BA = B_A
    spec_BA = start // allevents(plant_BA)
    sup_BA = synthesize(plant_BA, spec_BA, 'sup_BA', state_order_sources)

    plant = model_M1 // model_M2
    spec = REQ_Buffer // REQ_start // REQ_repair // allevents(plant)
    sup = synthesize(plant, spec, 'SUP', state_order_sources)

    isolated = [
        [M1, M2, sup_BA, generate, Buffer_fill, Blade, repair],
        [('21', 'M2_ON'), ('11', 'M1_ON')],
    ]
    return generate_ST_OPENPLC(
        [sup], [plant], actuators, 'Small_factory',
        Mask=Mask, Isolated=isolated, initial='start',
        output_dir=output_dir, event_order=components.event_order,
        state_order_sources=state_order_sources,
        transition_order=components.transition_order(isolated[0]),
    )


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()
    build(arguments.output_dir)
