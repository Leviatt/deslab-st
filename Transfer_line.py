"""Generate OpenPLC Structured Text for the transfer line with two main supervisors and auxiliary logic."""

from argparse import ArgumentParser
from pathlib import Path

from deslab import allevents

from example_models import ExampleComponents


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "ST_Generated"


def build(output_dir=DEFAULT_OUTPUT_DIR):
    actuators = dict([])

    actuators['start'] = 'GD_IN_0:ON:%IX100.0' #%IX100.0 %IX102.4'
    actuators['Piece_right'] = 'GD_IN_8:ON:%IX101.0' #%IX101.0 %IX103.1
    actuators['2'] = 'RE_M1:GD_IN_1:%IX100.1'  # M1_arriving
    actuators['M2_END'] = 'FE_M2E:GD_IN_6:%IX100.6'  # 4
    actuators['M2_ON'] = 'GD_OUT_7:ON:%QX100.7'  # 3
    actuators['M2_OFF'] = 'GD_OUT_7:OFF'
    actuators['M2_Bussy'] = 'GD_IN_6:ON:%IX100.6'
    actuators['Piece_at_review'] = 'FE_CP:GD_IN_7:%IX100.7'  # M1_arriving
    actuators['Piece_at_TU'] = 'RE_CP:GD_IN_7:%IX100.7'  # M1_arriving
    actuators['M1_arrived'] = 'FE_M1:GD_IN_1:%IX100.1'
    actuators['Clamp_on'] = 'GD_OUT_4:ON:%QX100.4'
    actuators['Clamp_off'] = 'GD_OUT_4:OFF'
    actuators['Clamped'] = "GD_IN_2:ON:%IX100.2"
    actuators['Piece_at_buffer'] = 'FE_B1:GD_IN_3:%IX100.3'
    actuators['BUFFER_Conveyor_ON'] = 'GD_OUT_5:ON:%QX100.5'
    actuators['BUFFER_Conveyor_OFF'] = 'GD_OUT_5:OFF'
    actuators['BLADE_ON'] = 'GD_OUT_6:ON:%QX100.6'
    actuators['BLADE_OFF'] = 'GD_OUT_6:OFF'
    actuators['BLADE_LIMIT'] = 'GD_IN_4:ON:%IX100.4'
    actuators['Buffer_out'] = 'FE_B1O:GD_IN_5:%IX100.5'
    actuators['BUFFER2_Conveyor_ON'] = 'GD_OUT_8:ON:%QX101.0'
    actuators['BUFFER2_Conveyor_OFF'] = 'GD_OUT_8:OFF'
    actuators['TU_Conveyor_ON'] = 'GD_OUT_9:ON:%QX101.1'  # 5
    actuators['TU_Conveyor_OFF'] = 'GD_OUT_9:OFF'
    actuators['TU_ARM_ON'] = 'GD_OUT_10:ON:%QX101.2'
    actuators['TU_ARM_OFF'] = 'GD_OUT_10:OFF'
    actuators['Piece_wrong'] = 'GD_IN_8:OFF'
    actuators['Piece_out'] = 'FE_PO:GD_IN_9:%IX101.1'  # 6
    actuators['Piece_reprocessed'] = 'FE_PR:GD_IN_11:%IX101.3'  # 8
    actuators['Piece_at_PyP'] = 'FE_AT:GD_IN_10:%IX101.2'
    actuators['Moving_Z'] = 'FE_MZ:GD_IN_12:%IX101.4'
    actuators['Rotating'] = 'FE_RO:GD_IN_13:%IX101.5'
    actuators['Z_ON'] = 'GD_OUT_15:ON:%QX101.7'
    actuators['Z_OFF'] = 'GD_OUT_15:OFF'
    actuators['GRAB_ON'] = 'GD_OUT_18:ON:%QX102.2'
    actuators['GRAB_OFF'] = 'GD_OUT_18:OFF'
    actuators['Rotate+_ON'] = 'GD_OUT_16:ON:%QX102.0'
    actuators['Rotate+_OFF'] = 'GD_OUT_16:OFF'
    actuators['Rotate-_ON'] = 'GD_OUT_17:ON:%QX102.1'
    actuators['Rotate-_OFF'] = 'GD_OUT_17:OFF'
    actuators['1'] = 'INTERN_1:ON'
    actuators['3'] = 'INTERN_3:ON'
    actuators['5'] = 'INTERN_5:ON'

    actuators['M1_Conveyor_ON'] = 'GD_OUT_0:ON:%QX100.0'  # 1
    actuators['M1_Conveyor_OFF'] = 'GD_OUT_0:OFF'

    Masks = dict([])

    Masks['GD_OUT_0'] = [('GD_OUT_1', '%QX100.1'), ('GD_OUT_2', '%QX100.2'),
                         ('GD_OUT_3', '%QX100.3')]  # ConveyorM1 -> EMITER, ARM_M1, ARM_SPEED_M1
    Masks['GD_OUT_10'] = [('GD_OUT_11', '%QX101.3'), ('GD_OUT_12', '%QX101.4'),
                          ('GD_OUT_13', '%QX101.5'),
                          ('GD_OUT_14', '%QX101.6')]  # ARM_TU -> ARMSPEED_TU, Conveyor_1REP, EMITREP,Conveyor2_REP

    components = ExampleComponents()

    # sup_M1

    Conveyor_M1 = components.component(
        'Conveyor_M1', 2, range(2),
        [(0, 'M1_Conveyor_ON', 1), (1, 'M1_Conveyor_OFF', 0)],
        uncontrollable=['M1_Conveyor_ON'],
    )

    M1_piece = components.component(
        'M1_piece', 2, range(2),
        [(0, 'M1_arrived', 1), (1, 'M1_Conveyor_OFF', 0)],
        uncontrollable=['M1_arrived'],
    )
    Conveyor_M1 = components.allow(Conveyor_M1, 'M1_arrived')

    # BUFFER 1

    Clamp = components.component(
        'Clamp', 2, range(2),
        [(0, 'Clamp_on', 1), (1, 'Clamp_off', 0)],
    )

    Blade = components.component(
        'Blade', 2, range(2),
        [(0, 'BLADE_ON', 1), (1, 'BLADE_OFF', 0)],
    )

    Clamp_REQ = components.component(
        'Camp_REQ', 3, range(3),
        [(0, 'Clamp_on', 1), (1, 'Clamped', 2), (2, 'Clamp_off', 0)],
        uncontrollable=['Clamped'],
    )
    Clamp = components.allow(Clamp, 'Clamped')

    Conveyor_buffer = components.component(
        'Conveyor_buffer', 2, range(2),
        [(0, 'BUFFER_Conveyor_ON', 1), (1, 'BUFFER_Conveyor_OFF', 0)],
    )

    Buffer_join = components.component(
        'Buffer_join', 12, range(12),
        [(0, 'BUFFER_Conveyor_ON', 1), (1, 'Piece_at_buffer', 2), (2, 'BUFFER_Conveyor_OFF', 3),
         (3, 'Clamp_on', 4), (4, 'Clamp_off', 5), (5, 'BLADE_ON', 6), (6, 'BLADE_LIMIT', 7),
         (7, 'BUFFER_Conveyor_ON', 8), (8, 'Buffer_out', 9), (9, 'BUFFER_Conveyor_OFF', 10),
         (10, 'BLADE_OFF', 11), (11, 'BLADE_LIMIT', 0)],
        uncontrollable=['Piece_at_buffer', 'Buffer_out'],
    )
    Conveyor_buffer = components.allow(Conveyor_buffer, 'Piece_at_buffer')
    Conveyor_buffer = components.allow(Conveyor_buffer, 'Buffer_out')
    Blade = components.allow(Blade, 'BLADE_LIMIT')

    event_2 = components.component(
        'event_2', 3, range(3),
        [(0, '2', 1), (1, 'BUFFER_Conveyor_ON', 2), (2, 'Buffer_out', 0),
         (2, 'BUFFER_Conveyor_ON', 2), (0, 'Piece_reprocessed', 1)],
        uncontrollable=['2', 'Buffer_out', 'Piece_reprocessed'],
    )
    Conveyor_buffer = components.allow(Conveyor_buffer, '2')
    Conveyor_buffer = components.allow(Conveyor_buffer, 'Piece_reprocessed')

    # M2

    M2 = components.component(
        'M2', 4, range(4),
        [(0, 'M2_ON', 1), (1, 'M2_Bussy', 2), (2, 'M2_OFF', 3), (3, 'M2_END', 0)],
        uncontrollable=['M2_ON', 'M2_Bussy', 'M2_END'],
    )

    # B2
    Conveyor_buffer2 = components.component(
        'Conveyor_buffer2', 2, range(2),
        [(0, 'BUFFER2_Conveyor_ON', 1), (1, 'BUFFER2_Conveyor_OFF', 0)],
    )
    Buffer2_join = components.component(
        'Buffer2_join', 5, range(5),
        [(0, 'M2_Bussy', 1), (1, 'M2_END', 2), (2, 'BUFFER2_Conveyor_ON', 3),
         (3, 'Piece_at_TU', 4), (4, 'BUFFER2_Conveyor_OFF', 0)],
        uncontrollable=['M2_Bussy', 'M2_END', 'Piece_at_TU'],
    )
    Conveyor_buffer2 = components.allow(Conveyor_buffer2, 'M2_END')
    Conveyor_buffer2 = components.allow(Conveyor_buffer2, 'M2_Bussy')
    Conveyor_buffer2 = components.allow(Conveyor_buffer2, 'Piece_at_TU')

    # ROBOT_ARM
    Pyp = components.component(
        'Pyp', 17, range(17),
        [(0, 'Piece_at_PyP', 1), (1, 'Z_ON', 2), (2, 'Moving_Z', 3), (3, 'GRAB_ON', 4),
         (4, 'Z_OFF', 5), (5, 'Moving_Z', 6), (6, 'Rotate+_ON', 7), (7, 'Rotating', 8),
         (8, 'Rotate+_OFF', 9), (9, 'Z_ON', 10), (10, 'Moving_Z', 11), (11, 'GRAB_OFF', 12),
         (12, 'Z_OFF', 13), (13, 'Moving_Z', 14), (14, 'Rotate-_ON', 15), (15, 'Rotating', 16),
         (16, 'Rotate-_OFF', 0)],
        uncontrollable=['Piece_at_PyP', 'Moving_Z', 'Rotating'],
    )

    # TU

    Conveyor_TU = components.component(
        'Conveyor_TU', 2, range(2),
        [(0, 'TU_Conveyor_ON', 1), (1, 'TU_Conveyor_OFF', 0)],
        uncontrollable=['TU_Conveyor_ON'],
    )

    ARM_TU = components.component(
        'ARM_TU', 2, range(2),
        [(0, 'TU_ARM_ON', 1), (1, 'TU_ARM_OFF', 0)],
    )

    TU_Function = components.component(
        'TU_Function', 9, range(9),
        [(0, 'TU_Conveyor_ON', 1), (1, 'Piece_at_review', 2), (2, 'Piece_right', 3),
         (3, 'Piece_out', 4), (4, 'TU_Conveyor_OFF', 0), (2, 'Piece_wrong', 5),
         (5, 'TU_ARM_ON', 6), (6, 'Piece_at_PyP', 7), (7, 'TU_ARM_OFF', 8),
         (8, 'TU_Conveyor_OFF', 0)],
        uncontrollable=['TU_Conveyor_ON', 'Piece_at_review', 'Piece_right', 'Piece_out', 'Piece_at_PyP', 'Piece_wrong'],
    )
    Conveyor_TU = components.allow(Conveyor_TU, 'Piece_at_review', 'Piece_right', 'Piece_out', 'Piece_at_PyP', 'Piece_wrong')

    M1_REQ = components.component(
        'M1_REQ', 2, [0],
        [(0, '1', 1), (1, '2', 0)],
        uncontrollable=['2'],
    )

    M2_REQ = components.component(
        'M2_REQ', 2, [0],
        [(0, '3', 1), (1, 'Piece_at_TU', 0)],
        uncontrollable=['Piece_at_TU'],
    )

    TU_REQ = components.component(
        'TU_REQ', 2, [0],
        [(0, '5', 1), (1, 'Piece_out', 0), (1, 'Piece_reprocessed', 0)],
        uncontrollable=['Piece_out', 'Piece_reprocessed'],
    )

    B1SP = components.component(
        'B1SP', 2, [0],
        [(0, '2', 1), (0, 'Piece_reprocessed', 1), (1, '3', 0)],
        uncontrollable=['2', 'Piece_reprocessed'],
    )

    B2SP = components.component(
        'B2SP', 2, [0],
        [(0, 'Piece_at_TU', 1), (1, '5', 0)],
        uncontrollable=['Piece_at_TU'],
    )

    TU_Function = components.complete_spec(TU_Function)
    Buffer2_join = components.complete_spec(Buffer2_join)
    M1_piece = components.complete_spec(M1_piece)
    Clamp_REQ = components.complete_spec(Clamp_REQ)
    Buffer_join = components.complete_spec(Buffer_join)
    event_2 = components.complete_spec(event_2)

    Plant_M1 = Conveyor_M1
    allm1 = allevents(Plant_M1)
    specm1 = M1_piece // allm1
    sup_M1 = components.synthesize(Plant_M1, specm1, 'sup_M1')

    Plant_Buffer_1 = Conveyor_buffer // Clamp // Blade
    allb1 = allevents(Plant_Buffer_1)
    specb1 = event_2 // Buffer_join // Clamp_REQ // allb1
    sup_B1 = components.synthesize(Plant_Buffer_1, specb1, 'sup_B1')

    Plant_Buffer_2 = Conveyor_buffer2
    allb2 = allevents(Plant_Buffer_2)
    specb2 = Buffer2_join // allb2
    sup_B2 = components.synthesize(Plant_Buffer_2, specb2, 'sup_B2')

    Plant_TU = Conveyor_TU // ARM_TU
    alltu = allevents(Plant_TU)
    spectu = TU_Function // alltu
    sup_TU = components.synthesize(Plant_TU, spectu, 'sup_TU')

    start = components.component(
        'start', 2, [1],
        [(0, 'start', 1), (1, '1', 1), (1, '3', 1), (1, '5', 1)],
        uncontrollable=['start'],
    )
    M2_REQ = components.allow(M2_REQ, 'start')
    start = components.complete_spec(start)

    # Plant with a start button.
    plant_2 = M1_REQ // M2_REQ // TU_REQ
    all_2 = allevents(plant_2)
    spec_2 = start // B1SP // all_2
    sup_2 = components.synthesize(plant_2, spec_2, 'sup_2')

    plant2_2 = M2_REQ // TU_REQ
    all2_2 = allevents(plant2_2)
    spec2_2 = B2SP // all2_2
    sup2_2 = components.synthesize(plant2_2, spec2_2, 'sup2_2')

    isolated = [
        [sup_M1, sup_B1, M2, sup_B2, sup_TU, Pyp],
        [('1', 'M1_Conveyor_ON'), ('3', 'M2_ON'), ('5', 'TU_Conveyor_ON')],
    ]
    return components.emit_st(
        [sup_2, sup2_2], [plant_2, plant2_2], actuators, 'transfer_line',
        Mask=Masks, Isolated=isolated, initial='start',
        output_dir=output_dir,
    )


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()
    build(arguments.output_dir)
