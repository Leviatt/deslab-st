"""Generate OpenPLC Structured Text for the transfer line with two main supervisors and auxiliary logic."""

from argparse import ArgumentParser
from pathlib import Path

from generator import process


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

    new_process = process(output_dir)

    # sup_M1

    Conveyor_M1 = new_process.new_automaton('Conveyor_M1')
    new_process.add_state(Conveyor_M1, 2, [], [True, True])
    new_process.add_transition(Conveyor_M1, [(0, 1), (1, 0)],
                               ['M1_Conveyor_ON', 'M1_Conveyor_OFF'], ['M1_Conveyor_ON'])

    M1_piece = new_process.new_automaton('M1_piece')
    new_process.add_state(M1_piece, 2, [], [True, True])
    new_process.add_transition(M1_piece, [(0, 1), (1, 0)], ['M1_arrived', 'M1_Conveyor_OFF'],
                               ['M1_arrived'])
    new_process.add_self_event(Conveyor_M1, 'M1_arrived')

    # BUFFER 1

    Clamp = new_process.new_automaton('Clamp')
    new_process.add_state(Clamp, 2, [], [True, True])
    new_process.add_transition(Clamp, [(0, 1), (1, 0)], ["Clamp_on", "Clamp_off"], [])

    Blade = new_process.new_automaton('Blade')
    new_process.add_state(Blade, 2, [], [True, True])
    new_process.add_transition(Blade, [(0, 1), (1, 0)], ["BLADE_ON", "BLADE_OFF"], [])

    Clamp_REQ = new_process.new_automaton('Camp_REQ')
    new_process.add_state(Clamp_REQ, 3, ["ON", "WAIT", "OFF"], [True, True, True])
    new_process.add_transition(Clamp_REQ, [(0, 1), (1, 2), (2, 0)],
                               ["Clamp_on", "Clamped", "Clamp_off"], ['Clamped'])
    new_process.add_self_event(Clamp, 'Clamped')

    Conveyor_buffer = new_process.new_automaton('Conveyor_buffer')
    new_process.add_state(Conveyor_buffer, 2, [], [True, True])
    new_process.add_transition(Conveyor_buffer, [(0, 1), (1, 0)],
                               ['BUFFER_Conveyor_ON', 'BUFFER_Conveyor_OFF'], [])

    Buffer_join = new_process.new_automaton('Buffer_join')
    new_process.add_state(Buffer_join, 12, [], [True, True, True, True, True, True, True, True,
                                                True, True, True, True])
    new_process.add_transition(Buffer_join, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9),
                                             (9, 10), (10, 11), (11, 0)],
                               ['BUFFER_Conveyor_ON', 'Piece_at_buffer', "BUFFER_Conveyor_OFF", 'Clamp_on', 'Clamp_off',
                                'BLADE_ON', 'BLADE_LIMIT', 'BUFFER_Conveyor_ON', 'Buffer_out', "BUFFER_Conveyor_OFF", 'BLADE_OFF',
                                'BLADE_LIMIT'], ['Piece_at_buffer', 'Buffer_out'])
    new_process.add_self_event(Conveyor_buffer, 'Piece_at_buffer')
    new_process.add_self_event(Conveyor_buffer, 'Buffer_out')
    new_process.add_self_event(Blade, 'BLADE_LIMIT')

    event_2 = new_process.new_automaton('event_2')
    new_process.add_state(event_2, 3, [], [True, True, True])
    new_process.add_transition(event_2, [(0, 1), (1, 2), (2, 0), (2, 2), (0, 1)], ['2', 'BUFFER_Conveyor_ON', 'Buffer_out',
                                                                                   'BUFFER_Conveyor_ON', 'Piece_reprocessed'],
                               ['2', 'Buffer_out', 'Piece_reprocessed'])
    new_process.add_self_event(Conveyor_buffer, '2')
    new_process.add_self_event(Conveyor_buffer, 'Piece_reprocessed')

    # M2

    M2 = new_process.new_automaton('M2')
    new_process.add_state(M2, 4, [], [True, True, True, True])
    new_process.add_transition(M2, [(0, 1), (1, 2), (2, 3), (3, 0)], ['M2_ON', 'M2_Bussy', 'M2_OFF', 'M2_END'],
                               ['M2_ON', 'M2_Bussy', 'M2_END'])

    # B2
    Conveyor_buffer2 = new_process.new_automaton('Conveyor_buffer2')
    new_process.add_state(Conveyor_buffer2, 2, [], [True, True])
    new_process.add_transition(Conveyor_buffer2, [(0, 1), (1, 0)], ['BUFFER2_Conveyor_ON', 'BUFFER2_Conveyor_OFF'], [])
    Buffer2_join = new_process.new_automaton('Buffer2_join')
    new_process.add_state(Buffer2_join, 5, [], [True, True, True, True, True])
    new_process.add_transition(Buffer2_join, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)],
                               ['M2_Bussy', 'M2_END', 'BUFFER2_Conveyor_ON', 'Piece_at_TU', 'BUFFER2_Conveyor_OFF'],
                               ['M2_Bussy', 'M2_END', 'Piece_at_TU'])
    new_process.add_self_event(Conveyor_buffer2, 'M2_END')
    new_process.add_self_event(Conveyor_buffer2, 'M2_Bussy')
    new_process.add_self_event(Conveyor_buffer2, 'Piece_at_TU')

    # ROBOT_ARM
    Pyp = new_process.new_automaton('Pyp')
    new_process.add_state(Pyp, 17, [],
                          [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True,
                           True])
    new_process.add_transition(Pyp, [(0, 1), (1, 2), (2, 3), (3, 4),
                                     (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12),
                                     (12, 13), (13, 14), (14, 15), (15, 16), (16, 0)],
                               ['Piece_at_PyP', 'Z_ON', 'Moving_Z', 'GRAB_ON',
                                'Z_OFF', 'Moving_Z', 'Rotate+_ON', 'Rotating', 'Rotate+_OFF', 'Z_ON', 'Moving_Z',
                                'GRAB_OFF',
                                'Z_OFF', 'Moving_Z', 'Rotate-_ON', 'Rotating', 'Rotate-_OFF'],
                               ['Piece_at_PyP', 'Moving_Z', 'Rotating'])

    # TU

    Conveyor_TU = new_process.new_automaton('Conveyor_TU')
    new_process.add_state(Conveyor_TU, 2, [], [True, True])
    new_process.add_transition(Conveyor_TU, [(0, 1), (1, 0)], ['TU_Conveyor_ON', 'TU_Conveyor_OFF'], ['TU_Conveyor_ON'])

    ARM_TU = new_process.new_automaton('ARM_TU')
    new_process.add_state(ARM_TU, 2, [], [True, True])
    new_process.add_transition(ARM_TU, [(0, 1), (1, 0)], ['TU_ARM_ON', 'TU_ARM_OFF'], [])

    TU_Function = new_process.new_automaton('TU_Function')
    new_process.add_state(TU_Function, 9, [], [True, True, True, True, True, True, True, True, True])
    new_process.add_transition(TU_Function, [(0, 1), (1, 2),
                                             (2, 3), (3, 4), (4, 0),
                                             (2, 5), (5, 6), (6, 7), (7, 8), (8, 0)],
                               ['TU_Conveyor_ON', 'Piece_at_review',  # Piece_at_TU ->5
                                'Piece_right', 'Piece_out', 'TU_Conveyor_OFF',
                                'Piece_wrong', 'TU_ARM_ON', 'Piece_at_PyP', 'TU_ARM_OFF', 'TU_Conveyor_OFF'],
                               ['TU_Conveyor_ON', 'Piece_at_review', 'Piece_right', 'Piece_out', 'Piece_at_PyP',
                                'Piece_wrong'])
    new_process.add_self_events(Conveyor_TU,
                                ['Piece_at_review', 'Piece_right', 'Piece_out', 'Piece_at_PyP', 'Piece_wrong'])

    M1_REQ = new_process.new_automaton('M1_REQ')
    new_process.add_state(M1_REQ, 2, [], [True])
    new_process.add_transition(M1_REQ, [(0, 1), (1, 0)], ['1', '2'], ['2'])

    M2_REQ = new_process.new_automaton('M2_REQ')
    new_process.add_state(M2_REQ, 2, [], [True])
    new_process.add_transition(M2_REQ, [(0, 1), (1, 0)], ['3', 'Piece_at_TU'], ['Piece_at_TU'])

    TU_REQ = new_process.new_automaton('TU_REQ')
    new_process.add_state(TU_REQ, 2, [], [True])
    new_process.add_transition(TU_REQ, [(0, 1), (1, 0), (1, 0)], ['5', 'Piece_out', 'Piece_reprocessed'],
                               ['Piece_out', 'Piece_reprocessed'])

    B1SP = new_process.new_automaton('B1SP')
    new_process.add_state(B1SP, 2, [], [True])
    new_process.add_transition(B1SP, [(0, 1), (0, 1), (1, 0)],
                               ['2', 'Piece_reprocessed', '3'], ['2', 'Piece_reprocessed'])

    B2SP = new_process.new_automaton('B2SP')  # EVENT 5
    new_process.add_state(B2SP, 2, [], [True])
    new_process.add_transition(B2SP, [(0, 1), (1, 0)],
                               ['Piece_at_TU', '5'], ['Piece_at_TU'])  # 4,5

    new_process.complete_spec(TU_Function)
    new_process.complete_spec(Buffer2_join)
    new_process.complete_spec(M1_piece)
    new_process.complete_spec(Clamp_REQ)
    new_process.complete_spec(Buffer_join)
    new_process.complete_spec(event_2)

    new_process.generate_all_automata()

    Plant_M1 = new_process.automata_syncronize([Conveyor_M1], name_sync='Plant_M1')  # , ARM_M1, ARM_M1_SPEED, Emiter_M1
    allm1 = new_process.all_events(Plant_M1, 'allm1')
    specm1 = new_process.automata_syncronize([M1_piece, allm1], name_sync='specm1')  # , start,
    sup_M1 = new_process.supcon(Plant_M1, specm1, 'sup_M1')

    new_process.load_automata([sup_M1, Plant_M1])

    Plant_Buffer_1 = new_process.automata_syncronize([Conveyor_buffer, Clamp, Blade], name_sync='Plant_Buffer_1')
    allb1 = new_process.all_events(Plant_Buffer_1, 'allb1')
    specb1 = new_process.automata_syncronize([event_2, Buffer_join, Clamp_REQ, allb1], name_sync='specb1')
    sup_B1 = new_process.supcon(Plant_Buffer_1, specb1, 'sup_B1')

    new_process.load_automata([sup_B1, Plant_Buffer_1])

    Plant_Buffer_2 = new_process.automata_syncronize([Conveyor_buffer2], name_sync='Plant_Buffer_2')
    allb2 = new_process.all_events(Plant_Buffer_2, 'allb2')
    specb2 = new_process.automata_syncronize([Buffer2_join, allb2], name_sync='specb2')
    sup_B2 = new_process.supcon(Plant_Buffer_2, specb2, 'sup_B2')

    new_process.load_automata([Plant_Buffer_2, sup_B2])

    Plant_TU = new_process.automata_syncronize([Conveyor_TU, ARM_TU], name_sync='Plant_TU')
    alltu = new_process.all_events(Plant_TU, 'alltu')
    spectu = new_process.automata_syncronize([TU_Function, alltu], name_sync='spectu')
    sup_TU = new_process.supcon(Plant_TU, spectu, 'sup_TU')

    new_process.load_automata([Plant_TU, sup_TU])

    start = new_process.new_automaton('start')
    new_process.add_state(start, 2, ["waiting", 'start'], [False, True])
    new_process.add_transition(start, [(0, 1), (1, 1), (1, 1), (1, 1)], ['start', '1', '3', '5'],
                               ['start'])
    new_process.add_self_event(M2_REQ, 'start')
    new_process.complete_spec(start)
    new_process.generate_all_automata()

    # Plant with a start button.
    plant_2 = new_process.automata_syncronize([M1_REQ, M2_REQ, TU_REQ], name_sync='plant_2')
    all_2 = new_process.all_events(plant_2, 'all_2')
    spec_2 = new_process.automata_syncronize([start, B1SP, all_2], name_sync='spec_2')
    sup_2 = new_process.supcon(plant_2, spec_2, 'sup_2')

    new_process.load_automata([plant_2, sup_2])

    plant2_2 = new_process.automata_syncronize([M2_REQ, TU_REQ], name_sync='plant2_2')
    all2_2 = new_process.all_events(plant2_2, 'all2_2')
    spec2_2 = new_process.automata_syncronize([B2SP, all2_2], name_sync='spec2_2')
    sup2_2 = new_process.supcon(plant2_2, spec2_2, 'sup2_2')

    new_process.load_automata([plant2_2, sup2_2])

    isolated = [
        [sup_M1, sup_B1, M2, sup_B2, sup_TU, Pyp],
        [('1', 'M1_Conveyor_ON'), ('3', 'M2_ON'), ('5', 'TU_Conveyor_ON')],
    ]
    return new_process.generate_ST_OPENPLC(
        [sup_2, sup2_2], [plant_2, plant2_2], actuators, 'transfer_line',
        Mask=Masks, Isolated=isolated, initial='start',
    )


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()
    build(arguments.output_dir)
