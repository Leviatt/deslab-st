"""Generate OpenPLC Structured Text for the assembly line with five local supervisors."""

from argparse import ArgumentParser
from pathlib import Path

from deslab import allevents

from example_models import ExampleComponents


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "ST_Generated"


def build(output_dir=DEFAULT_OUTPUT_DIR):
    actuators = dict([])
    actuators['lids_conveyor_on'] = 'GD_OUT_2:ON:%QX100.2'
    actuators['lids_conveyor_off'] = 'GD_OUT_2:OFF'
    actuators['bases_conveyor_on'] = 'GD_OUT_3:ON:%QX100.3'
    actuators['bases_conveyor_off'] = 'GD_OUT_3:OFF'
    actuators['Lid_clamp_on'] = 'GD_OUT_4:ON:%QX100.4'
    actuators['Lid_clamp_off'] = 'GD_OUT_4:OFF'
    actuators['Base_clamp_on'] = 'GD_OUT_5:ON:%QX100.5'
    actuators['Base_clamp_off'] = 'GD_OUT_5:OFF'
    actuators['z_axis_on'] = 'GD_OUT_6:ON:%QX100.6'
    actuators['z_axis_off'] = 'GD_OUT_6:OFF'
    actuators['grab_on'] = 'GD_OUT_7:ON:%QX100.7'
    actuators['grab_off'] = 'GD_OUT_7:OFF'
    actuators['x_axis_on'] = 'GD_OUT_8:ON:%QX101.0'
    actuators['x_axis_off'] = 'GD_OUT_8:OFF'
    actuators['blade_on'] = 'GD_OUT_9:ON:%QX101.1'
    actuators['blade_off'] = 'GD_OUT_9:OFF'

    actuators['start_on'] = 'GD_IN_15:ON:%IX100.15'  # %IX100.15 %IX102.7'

    actuators['lid_at_place_FE'] = 'FE_LaP:GD_IN_2:%IX100.2'
    actuators['lid_clampled'] = "GD_IN_4:ON:%IX100.4"
    actuators['base_at_place_FE'] = 'FE_BaP:GD_IN_3:%IX100.3'
    actuators['part_leaving_FE'] = 'FE_PaL:GD_IN_9:%IX101.1'
    actuators['base_clampled'] = "GD_IN_5:ON:%IX100.5"
    actuators['z_movement_finish'] = 'FE_Zag:GD_IN_6:%IX100.6'
    actuators['x_movement_finish'] = 'FE_Xag:GD_IN_7:%IX100.7'
    actuators['blade_pos_limit_on'] = 'GD_IN_8:ON:%IX101.0'

    actuators['gen_base'] = 'GD_IN_10:ON:%IX102.5'
    actuators['gen_lid'] = 'GD_IN_11:ON:%IX102.6'

    Mask = dict([])
    Mask['GD_IN_10'] = [('GD_OUT_12', '%QX101.2')]
    Mask['GD_IN_11'] = [('GD_OUT_13', '%QX101.3')]

    components = ExampleComponents()

    Lids_conveyor = components.component(
        'lids_conveyor', 2, range(2),
        [(0, 'lids_conveyor_on', 1), (1, 'lids_conveyor_off', 0)],
    )

    start_lid_conveyor = components.component(
        'start', 2, [1],
        [(0, 'start_on', 1), (1, 'lids_conveyor_on', 1)],
        uncontrollable=['start_on'],
    )
    Lids_conveyor = components.allow(Lids_conveyor, 'start_on')

    Lid_clamp = components.component(
        'Lid_clamp', 2, range(2),
        [(0, 'Lid_clamp_on', 1), (1, 'Lid_clamp_off', 0)],
    )

    Lid_clamp_REQ = components.component(
        'Lid_clamp_REQ', 3, [0],
        [(0, 'Lid_clamp_on', 1), (1, 'lid_clampled', 2), (2, 'Lid_clamp_off', 0)],
        uncontrollable=['lid_clampled'],
    )
    Lid_clamp = components.allow(Lid_clamp, 'lid_clampled')

    buffer_lid = components.component(
        'buffer_lid', 5, [0],
        [(0, 'lids_conveyor_on', 1), (1, 'lid_at_place_FE', 2), (2, 'lids_conveyor_off', 3),
         (3, 'Lid_clamp_on', 4), (4, 'Lid_clamp_off', 0)],
        uncontrollable=['lid_at_place_FE'],
    )

    Lid_clamp = components.allow(Lid_clamp, 'lid_at_place_FE')
    Lids_conveyor = components.allow(Lids_conveyor, 'lid_at_place_FE')

    Grab = components.component(
        'grab', 2, range(2),
        [(0, 'grab_on', 1), (1, 'grab_off', 0)],
    )

    z_axis = components.component(
        'z_axis', 4, range(4),
        [(0, 'z_axis_on', 1), (1, 'z_movement_finish', 2), (2, 'z_axis_off', 3),
         (3, 'z_movement_finish', 0)],
        uncontrollable=['z_movement_finish'],
    )

    x_axis = components.component(
        'x_axis', 4, range(4),
        [(0, 'x_axis_on', 1), (1, 'x_movement_finish', 2), (2, 'x_axis_off', 3),
         (3, 'x_movement_finish', 0)],
        uncontrollable=['x_movement_finish'],
    )

    arm_behaviour = components.component(
        'buffer_arm', 16, [0],
        [(0, 'lid_clampled', 1), (1, 'z_axis_on', 2), (2, 'z_movement_finish', 3),
         (3, 'grab_on', 4), (4, 'Lid_clamp_off', 5), (5, 'z_axis_off', 6),
         (6, 'z_movement_finish', 7), (7, 'x_axis_on', 8), (8, 'x_movement_finish', 9),
         (9, 'z_axis_on', 10), (10, 'z_movement_finish', 11), (11, 'grab_off', 12),
         (12, 'z_axis_off', 13), (13, 'z_movement_finish', 14), (14, 'x_axis_off', 15),
         (15, 'x_movement_finish', 0)],
        uncontrollable=['lid_clampled', 'z_movement_finish', 'x_movement_finish'],
    )

    Base_conveyor = components.component(
        'Base_conveyor', 2, range(2),
        [(0, 'bases_conveyor_on', 1), (1, 'bases_conveyor_off', 0)],
    )

    Base_clamp = components.component(
        'Base_clamp', 2, range(2),
        [(0, 'Base_clamp_on', 1), (1, 'Base_clamp_off', 0)],
    )

    Base_clamp_REQ = components.component(
        'Base_clamp_REQ', 3, [0],
        [(0, 'Base_clamp_on', 1), (1, 'base_clampled', 2), (2, 'Base_clamp_off', 0)],
        uncontrollable=['base_clampled'],
    )
    Base_clamp = components.allow(Base_clamp, 'base_clampled')

    start_base_conveyor = components.component(
        'start_2', 2, [1],
        [(0, 'start_on', 1), (1, 'bases_conveyor_on', 1)],
        uncontrollable=['start_on'],
    )
    Base_conveyor = components.allow(Base_conveyor, 'start_on')

    buffer_base = components.component(
        'buffer_base', 5, [0],
        [(0, 'bases_conveyor_on', 1), (1, 'base_at_place_FE', 2), (2, 'bases_conveyor_off', 3),
         (3, 'Base_clamp_on', 4), (4, 'Base_clamp_off', 0)],
        uncontrollable=['base_at_place_FE'],
    )

    Base_clamp = components.allow(Base_clamp, 'base_at_place_FE')
    Base_conveyor = components.allow(Base_conveyor, 'base_at_place_FE')

    Blade = components.component(
        'blade', 2, range(2),
        [(0, 'blade_on', 1), (1, 'blade_off', 0)],
    )

    complete_piece = components.component(
        'complete_piece', 5, [0],
        [(0, 'Base_clamp_on', 1), (1, 'base_clampled', 2), (2, 'x_axis_on', 3),
         (3, 'grab_off', 4), (4, 'Base_clamp_off', 0)],
        uncontrollable=['base_clampled'],
    )

    leave = components.component(
        'leave', 6, [0],
        [(0, 'Base_clamp_on', 1), (1, 'Base_clamp_off', 2), (2, 'blade_on', 3),
         (3, 'blade_pos_limit_on', 4), (4, 'part_leaving_FE', 5), (5, 'blade_off', 0)],
        uncontrollable=['blade_pos_limit_on', 'part_leaving_FE'],
    )
    Blade = components.allow(Blade, 'blade_pos_limit_on')
    Blade = components.allow(Blade, 'part_leaving_FE')

    start_lid_conveyor = components.complete_spec(start_lid_conveyor)
    buffer_lid = components.complete_spec(buffer_lid)
    Lid_clamp_REQ = components.complete_spec(Lid_clamp_REQ)

    start_base_conveyor = components.complete_spec(start_base_conveyor)
    buffer_base = components.complete_spec(buffer_base)
    Base_clamp_REQ = components.complete_spec(Base_clamp_REQ)

    arm_behaviour = components.complete_spec(arm_behaviour)
    complete_piece = components.complete_spec(complete_piece)
    leave = components.complete_spec(leave)

    plant1 = Lids_conveyor // Lid_clamp
    all = allevents(plant1)
    spec = buffer_lid // Lid_clamp_REQ // start_lid_conveyor // all
    sup1 = components.synthesize(plant1, spec, 'SUP')

    plant2 = Lid_clamp // Grab // z_axis // x_axis
    all2 = allevents(plant2)
    spec2 = arm_behaviour // all2
    sup2 = components.synthesize(plant2, spec2, 'sup2')

    plant3 = Base_clamp // Grab // x_axis
    all3 = allevents(plant3)
    spec3 = complete_piece // all3
    sup3 = components.synthesize(plant3, spec3, 'sup3')

    plant4 = Base_conveyor // Base_clamp
    all4 = allevents(plant4)
    spec4 = buffer_base // Base_clamp_REQ // start_base_conveyor // all4
    sup4 = components.synthesize(plant4, spec4, 'sup4')

    plant5 = Base_clamp // Blade
    all5 = allevents(plant5)
    spec5 = leave // all5
    sup5 = components.synthesize(plant5, spec5, 'sup5')

    return components.emit_st(
        [sup1, sup2, sup3, sup4, sup5],
        [plant1, plant2, plant3, plant4, plant5],
        actuators, 'Assembly_line', Mask=Mask,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()
    build(arguments.output_dir)
