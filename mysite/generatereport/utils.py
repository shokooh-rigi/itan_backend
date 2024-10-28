from .models import *
from ..sheetcreator.models import *



def get_field_value(field_set, field_name, default=""):
    val = field_set.get(field_name, {}).get('value', default)
    # handle None
    if not val:
        val = default
    return {
        'value': val,
        'note': field_set.get(field_name, {}).get('note', '')
    }
    
def get_field_note_and_append(field_set, field_name, notes, note_count):
    if field_name in field_set and field_set[field_name].get('note'):
        note_count += 1
        note_marker = str(note_count * "*")
        notes.append(f"{note_marker} {field_set[field_name]['note']}")
        return note_marker, note_count
    return "", note_count

def populate_notes_and_fields(field_names, design_set, actual_set, equipment_data, notes, note_count):
    for field_name, key in field_names.items():
        equipment_data[key] = {
            'design': get_field_value(design_set, field_name),
            'actual': get_field_value(actual_set, field_name)
        }
        design_marker, note_count = get_field_note_and_append(design_set, field_name, notes, note_count)
        actual_marker, note_count = get_field_note_and_append(actual_set, field_name, notes, note_count)
        if design_marker:
            equipment_data[key]['design'] += f" {design_marker}".strip()
        if actual_marker:
            equipment_data[key]['actual'] += f" {actual_marker}".strip()
    return note_count



def handle_defaults(equipment_list, equipment_type):
    return equipment_list

def handle_empty_fields(equipment_list, equipment_typ=""):
    data = []
    for i in range(len(equipment_list)):
        equipment_data = equipment_list[i]
        for k1, v1 in equipment_data.items():
            if not v1:
                equipment_data[k1] = '----'
        data.append(equipment_data)
    return data

def handle_uppercase_fields(equipment_list, equipment_type):
    data = []
    for i in range(len(equipment_list)):
        equipment_data = equipment_list[i]
        for key, val in equipment_data.items():
            if key == 'note':
                continue
            if isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    if sub_key == 'note':
                        continue
                    equipment_data[key][sub_key] = str(sub_val).upper()
            else:
                equipment_data[key] = str(val).upper()
        data.append(equipment_data)
    return data

def set_field_value(equipment_list):
    data = []
    for i in range(len(equipment_list)):
        equipment_data = equipment_list[i]
        for k1, v1 in equipment_data.items():
            if isinstance(v1, dict):
                if "@" in str(v1['value']):
                    _val = v1['value'].replace("@", "").strip()
                    equipment_data[k1] = _val
                else:
                    equipment_data[k1] = v1['value']
        data.append(equipment_data)
    return data

def handle_notes(equipment_list, equipment_type):
    equipments_for_this_page = []
    notes_for_this_page = []

    field_notes = {
        # 'some note...': '**',
    }
    if equipment_type == 'air_terminal':
        count = 1
    else:
        count = 0
    for i in range(len(equipment_list)):
        equipment_data = equipment_list[i]
        # default notes
        eq_notes = equipment_data.get('note', '')
        for _n in eq_notes:
            if _n and (_n not in notes_for_this_page):
                notes_for_this_page.append(_n.strip())
        # field notes
        for k,  v in equipment_data.items():
            # skip general fields with no note
            if isinstance(v, dict):
                _n = v.get('note', '').strip()
                if _n:
                    # check if its already in field_notes
                    if _n in field_notes.keys():
                        equipment_data[k]['value'] += f" {field_notes[_n]}"
                    else:
                        count += 1
                        note_marker = str(count * "*")
                        notes_for_this_page.append(f"{note_marker} {_n}".strip())
                        field_notes[_n] = note_marker
                        equipment_data[k]['value'] += f" {note_marker}"

        equipments_for_this_page.append(equipment_data)

    regular_notes = [note for note in notes_for_this_page if not note.startswith('*')]
    asterisk_notes = [note for note in notes_for_this_page if note.startswith('*')]
    regular_notes.sort()
    asterisk_notes.sort(key=lambda note: (count_asterisks(note), note))

    notes_for_this_page = regular_notes + asterisk_notes
    # remove empty notes
    notes_for_this_page = [note for note in notes_for_this_page if note]
    notes_for_this_page = " | ".join(notes_for_this_page)

    return equipments_for_this_page, notes_for_this_page


def count_asterisks(text):
    return len(text) - len(text.lstrip('*'))

def fetch_field_data(
        equipment, 
        field_name, 
        default_design_value='', 
        default_actual_value='', 
        is_dict=True, 
        actual_field=None
    ):
    """Fetches design and actual data for a given field name, or returns default values."""
    custom_fields = equipment.form_fields["design"]
    actual_fields = equipment.form_fields["actual"]
    
    design_value = custom_fields.get(field_name, {}).get('value', default_design_value)
    actual_value = actual_fields.get(field_name, {}).get('value', default_actual_value if not is_dict else 'N.M.')
    
    if design_value == '@':
        design_value = ''
    if actual_value == '@':
        actual_value = ''

    if is_dict:
        return {
            'design': design_value if design_value else default_design_value,
            'actual': actual_value if actual_value else default_actual_value
        }
    else:
        return design_value if design_value else default_design_value

def fetch_air_mov_data(equipment):
    """Fetches and returns equipment data."""
    design_set = equipment.form_fields["design"]
    actual_set = equipment.form_fields["actual"]

    equipment_data = {
        'fan_no': equipment.fan_no,
        'location': equipment.location,
        'area_served': equipment.area_served,
        'manufacturer': equipment.manufacturer.name.upper() if equipment.manufacturer else '',
        'model_no': equipment.model_number,
        'serial_no': get_field_value(actual_set, 'Serial / Job No.'),
        'total_cfm_fan_design': get_field_value(design_set, 'Total C.F.M. Fan'),
        'total_cfm_fan_actual': get_field_value(actual_set, 'Total C.F.M. Fan'),
        'air_temp_in_cooling_design': get_field_value(design_set, 'Air Temp. In Cooling'),
        'air_temp_in_cooling_actual': get_field_value(actual_set, 'Air Temp. In Cooling'),
        'total_cfm_outlets_design': get_field_value(design_set, 'Total C.F.M. Outlets'),
        'total_cfm_outlets_actual': get_field_value(actual_set, 'Total C.F.M. Outlets'),
        'air_temp_out_cooling_design': get_field_value(design_set, 'Air Temp. Out Cooling'),
        'air_temp_out_cooling_actual': get_field_value(actual_set, 'Air Temp. Out Cooling'),
        'return_air_cfm_design': get_field_value(design_set, 'Return Air C.F.M.'),
        'return_air_cfm_actual': get_field_value(actual_set, 'Return Air C.F.M.'),
        'rh_design': get_field_value(design_set, 'RH %'),
        'rh_actual': get_field_value(actual_set, 'RH %'),
        'outdoor_air_cfm_design': get_field_value(design_set, 'Outdoor Air C.F.M.'),
        'outdoor_air_cfm_actual': get_field_value(actual_set, 'Outdoor Air C.F.M.'),
        'air_temp_in_heating_design': get_field_value(design_set, 'Air Temp. In Heating'),
        'air_temp_in_heating_actual': get_field_value(actual_set, 'Air Temp. In Heating'),
        'total_sp_ext_sp_design': get_field_value(design_set, 'Total SP (Ext. SP)', default='N.S.'),
        'total_sp_ext_sp_actual': get_field_value(actual_set, 'Total SP (Ext. SP)', default='N.M.'),
        'air_temp_out_heating_design': get_field_value(design_set, 'Air Temp. Out Heating'),
        'air_temp_out_heating_actual': get_field_value(actual_set, 'Air Temp. Out Heating'),
        'fan_unit_suction_pressure_design': get_field_value(design_set, 'Fan (Unit) Suction Pressure', default='N.S.'),
        'fan_unit_suction_pressure_actual': get_field_value(actual_set, 'Fan (Unit) Suction Pressure', default='N.M.'),
        'ambient_temp_design': get_field_value(design_set, 'Ambient Temp.'),
        'ambient_temp_actual': get_field_value(actual_set, 'Ambient Temp.'),
        'discharge_pressure_fan_unit_design': get_field_value(design_set, 'Discharge Pressure, Fan / Unit', default='N.S.'),
        'discharge_pressure_fan_unit_actual': get_field_value(actual_set, 'Discharge Pressure, Fan / Unit', default='N.M.'),
        'oa_damper_poss_design': get_field_value(design_set, 'O.A. Damper Poss.'),
        'oa_damper_poss_actual': get_field_value(actual_set, 'O.A. Damper Poss.'),
        'fan_rpm_design': get_field_value(design_set, 'Fan R.P.M.', default='D.D.'),
        'fan_rpm_actual': get_field_value(actual_set, 'Fan R.P.M.', default='D.D.'),
        'gpm_design': get_field_value(design_set, 'GPM'),
        'gpm_actual': get_field_value(actual_set, 'GPM'),
        'hp_design': get_field_value(design_set, 'H.P.'),
        'belt_size_actual': get_field_value(actual_set, 'Belt Size', default='N.A.'),
        'motor_pully_actual': get_field_value(actual_set, 'Motor Pully', default='N.A.'),
        'voltage_design': get_field_value(design_set, 'Voltage'),
        'voltage_actual': get_field_value(actual_set, 'Voltage'),
        'fan_pully_actual': get_field_value(actual_set, 'Fan Pully', default='N.A.'),
        'phase_design': get_field_value(design_set, 'Phase'),
        'phase_actual': get_field_value(actual_set, 'Phase'),
        'c_to_c_actual': get_field_value(actual_set, 'C to C', default='N.A.'),
        'amperage_design': get_field_value(design_set, 'Amperage'),
        'amperage_actual': get_field_value(actual_set, 'Amperage'),
        'motor_shaft_actual': get_field_value(actual_set, 'Motor Shaft', default='N.A.'),
        'bhp_calc_design': get_field_value(design_set, 'B.H.P. (Calc.)', default='N.S.'),
        'bhp_calc_actual': get_field_value(actual_set, 'B.H.P. (Calc.)'),
        'fan_shaft_actual': get_field_value(actual_set, 'Fan Shaft', default='N.A.'),
        'frame_design': get_field_value(design_set, 'Frame', default='N.S.'),
        'frame_actual': get_field_value(actual_set, 'Frame'),
        'vfd_hz_actual': get_field_value(actual_set, 'VFD / HZ', default="N.A."),
        'sf_code_design': get_field_value(design_set, 'S.F. / Code', default='N.S.'),
        'filter_size_actual': get_field_value(actual_set, 'Filter Size', default="N.A."),
        'motor_rpm_design': get_field_value(design_set, 'Motor RPM', default='D.D.'),
        'motor_rpm_actual': get_field_value(actual_set, 'Motor RPM', default='D.D.'),
        'filter_model_actual': get_field_value(actual_set, 'Filter Model', default="N.A."),
        'direct_drive': get_field_value(design_set, 'Direct Drive'),
        'belt_drive': get_field_value(design_set, 'Belt Drive'),
        'max_speed': get_field_value(design_set, 'Max Speed'),
        'med_speed': get_field_value(design_set, 'Med Speed'),
        'min_speed': get_field_value(design_set, 'Min Speed'),
        'note': [get_field_value(design_set, 'Note')["value"], get_field_value(actual_set, 'Note')["value"]],
    }

    return equipment_data

def fetch_vav_data(this_sheet_equipments):
    data = []
    
    for this_sheet_equipment in this_sheet_equipments:
        design_field_set = this_sheet_equipment.form_fields["design"]
        actual_field_set = this_sheet_equipment.form_fields["actual"]
        equipment_data = {
            'id': this_sheet_equipment.id,
            'inherit': this_sheet_equipment.equipment_type.test_sheet.inheritance,
            'address': get_field_value(design_field_set, 'Address'),
            'code': this_sheet_equipment.code,
            'type': get_field_value(design_field_set, 'Type'),
            'size_kw': get_field_value(design_field_set, 'Size / KW'),
            'fan': get_field_value(design_field_set, 'Fan %'),
            'fan_cfm': get_field_value(design_field_set, 'Fan CFM'),
            'kf': get_field_value(actual_field_set, 'K.F.'),
            'min_fan_cfm': get_field_value(actual_field_set, 'Min. / Fan CFM'),
            'model_number': this_sheet_equipment.model_number,
            'hp': get_field_value(actual_field_set, 'H.P.'),
            'make': this_sheet_equipment.manufacturer,
            'fan_volt': get_field_value(actual_field_set, 'Fan volt'),
            'fan_amp': get_field_value(actual_field_set, 'Fan Amp'),
            't_in': get_field_value(actual_field_set, 'T In'),
            'fan_va': get_field_value(actual_field_set, 'Fan V / A'),
            't_out': get_field_value(actual_field_set, 'T Out'),
            'min_cfm_design': get_field_value(design_field_set, 'Min. CFM'),
            'min_cfm_actual': get_field_value(actual_field_set, 'Min. CFM'),
            'max_cfm_design': get_field_value(design_field_set, 'Max. CFM'),
            'max_cfm_actual': get_field_value(actual_field_set, 'Max. CFM'),
            "heat_va": get_field_value(actual_field_set, 'Heat V / A'),
            "heat_va_actual": get_field_value(actual_field_set, 'Heat V / A Actual'),
            "note": [get_field_value(design_field_set, 'Note')["value"], get_field_value(actual_field_set, 'Note')["value"]],
        }
        if equipment_data['fan']['value']:
            equipment_data['fan']['value'] = f"{equipment_data['fan']['value']} %"

        eq_types = {
            'HW': 'Hot Water',
            'RH': 'Reheat',
            'CO': 'Cooling Only',
            'FPS': 'Fan Powered Series',
            'FPP': 'Fan Powered Parallel',
        }
        if equipment_data['type']['value'] in eq_types:
            tmp = f"{equipment_data['type']['value']}: {eq_types[equipment_data['type']['value']]}".strip()
            if tmp not in equipment_data['note']:
                equipment_data['note'].append(tmp)

        data.append(equipment_data)

    return data


def fetch_terminal_data(terminals, _type):
    if not terminals:
        equipment_list = []
        page = {
            'type': 'TERMINAL',
            'eq_name': "Terminal",
            'system': "",
            'rows': equipment_list,
            'title': "Terminal",
            'total': {},
            'notes': ""
        }
        # Add empty rows to fill the page
        equipment_in_page = 18  # 21 total rows - 3 header rows
        page['empty_rows'] = [{} for _ in range(equipment_in_page - len(equipment_list))]
        return page

    map_type = {
        1: 'SUPPLY',
        2: 'RETURN',
        3: 'OUTSIDE AIR',
        4: 'EXHAUST',
        5: 'OTHER'
    }
    _type = map_type.get(_type, '')
    equipment_list = []
    for terminal in terminals:
        design_field_set = terminal.form_fields["design"]
        actual_field_set = terminal.form_fields["actual"]

        equipment_data = {
            'room_no': get_field_value(design_field_set, "Room No."),
            'outlet_no': terminal.outlet_no,
            'code': get_field_value(design_field_set, "Code"),
            'size': get_field_value(design_field_set, "Size"),
            'ak_factor': get_field_value(design_field_set, "AK Factor", "*"),
            'fpm_design': get_field_value(design_field_set, "FPM", "*"),
            'fpm_initial': get_field_value(actual_field_set, "Initial FPM", "*"),
            'fpm_final': get_field_value(actual_field_set, "Final FPM", "*"),
            'cfm_design': get_field_value(design_field_set, "CFM"),
            'cfm_initial': get_field_value(actual_field_set, "Initial CFM"),
            'cfm_final': get_field_value(actual_field_set, "Final CFM"),
            'note': [get_field_value(design_field_set, 'Note')["value"], get_field_value(actual_field_set, 'Note')["value"]],
            'title': terminal.fan_no,
            'type': _type,
        }

        if (str(equipment_data['cfm_design']['value']) == "0") or (equipment_data['cfm_design']['note']) or (not equipment_data['cfm_design']['value']):
            if not equipment_data['fpm_design']['value']:
                equipment_data['fpm_design']['value'] = "*"
        if (str(equipment_data['cfm_initial']['value']) == "0") or (equipment_data['cfm_initial']['note']) or (not equipment_data['cfm_initial']['value']):
            if not equipment_data['fpm_initial']['value']:
                equipment_data['fpm_initial']['value'] = "*"
        if (str(equipment_data['cfm_final']['value']) == "0") or (equipment_data['cfm_final']['note']) or (not equipment_data['cfm_final']['value']):
            if not equipment_data['fpm_final']['value']:
                equipment_data['fpm_final']['value'] = "*"
        
        # round fpm design, fpm initial and fpm final
        for key in ['fpm_design', 'fpm_initial', 'fpm_final']:
            try:
                equipment_data[key]['value'] = round(float(equipment_data[key]['value']))
            except ValueError:
                pass

        equipment_list.append(equipment_data)

    # Calculate totals
    total_cfm_design = sum(
        int(e['cfm_design']["value"]) for e in equipment_list 
        if e['cfm_design']["value"] and e['cfm_design']["value"] != "*"
    )
    total_cfm_initial = sum(
        int(e['cfm_initial']['value']) for e in equipment_list 
        if e['cfm_initial']["value"] and e['cfm_initial']["value"] != "*"
    )
    total_cfm_final = sum(
        int(e['cfm_final']['value']) for e in equipment_list 
        if e['cfm_final']['value'] and e['cfm_final']['value'] != "*"
    )
    
    # Notes
    equipment_list, notes = handle_notes(equipment_list, "air_terminal")
    # clean up fields and use values not notes
    equipment_list = set_field_value(equipment_list)
    # Clean up any fields that are empty or None
    equipment_list = handle_empty_fields(equipment_list, "air_terminal")
    # Convert all values to upper case
    equipment_list = handle_uppercase_fields(equipment_list, "air_terminal")

    # Set total to empty string if it's zero
    if total_cfm_design == 0:
        total_cfm_design = ""
    if total_cfm_initial == 0:
        total_cfm_initial = ""
    if total_cfm_final == 0:
        total_cfm_final = ""

    if terminals[0].parent:
        this_title = terminals[0].parent.name or terminals[0].parent.fan_no
    else:
        this_title = terminals[0].fan_no
    page = {
        'type': 'TERMINAL',
        'eq_name': "Terminal",
        'system': this_title,
        'rows': equipment_list,
        'title': f"{this_title} {_type}",
        'total': {
            'footer': f'TOTAL {_type} {this_title}',
            'cfm_design': total_cfm_design,
            'cfm_initial': total_cfm_initial,
            'cfm_final': total_cfm_final,
        },
        'notes': notes
    }

    if (terminals[0].parent) and 'V.A.V' in (terminals[0].parent.equipment_type.test_sheet.name):
        design_code = terminals[0].parent.code
        page['system'] = "Existing Supply".upper()
        page['system'] = design_code.upper()
        page['title'] = f"{design_code} {_type}".upper()
        page['total']['footer'] = f'TOTAL {_type} {design_code}'.upper()

    # Add empty rows to fill the page
    equipment_in_page = 18  # 21 total rows - 3 header rows
    page['empty_rows'] = [{} for _ in range(equipment_in_page - len(equipment_list))]
    
    return page

def fetch_pump_data(pumps):
    data = []
    for p in pumps:
        design_field_set = p.form_fields["design"]
        actual_field_set = p.form_fields["actual"]

        equipment_data = {
            'pump_no': p.model_number,
            'manufacturer': p.manufacturer.name.upper() if p.manufacturer else '',
            'serial_no': get_field_value(actual_field_set, "Serial No."),
            'model_size': f"{p.model_number} / {get_field_value(design_field_set, 'Size')}",
            'impeller_rpm': f"{get_field_value(design_field_set, 'Impeller')} / {get_field_value(design_field_set, 'RPM')}",
            'maxwk_mfgdate': f"{get_field_value(design_field_set, 'Max. Wk. Pr.')} / {get_field_value(design_field_set, 'Mfg. Date')}",
            'design_gpm': get_field_value(design_field_set, 'Design GPM'),
            'design_ft': get_field_value(design_field_set, 'Design FT'),
            'design_bhp': get_field_value(actual_field_set, 'Design BHP'),
            'actual_gpm': get_field_value(actual_field_set, 'Actual GPM'),
            'actual_ft': get_field_value(actual_field_set, 'Actual FT'),
            'actual_bhp': get_field_value(actual_field_set, 'Actual BHP'),
            'discharge_gpm': get_field_value(actual_field_set, 'Discharge GPM'),
            'discharge_ft': get_field_value(actual_field_set, 'Discharge FT'),
            'discharge_bhp': get_field_value(actual_field_set, 'Discharge BHP'),
            'suction_gpm': get_field_value(actual_field_set, 'Suction GPM'),
            'suction_ft': get_field_value(actual_field_set, 'Suction FT'),
            'suction_bhp': get_field_value(actual_field_set, 'Suction BHP'),
            'discharge_suction': get_field_value(actual_field_set, 'Discharge / Suction'),
            'motor_mfg': get_field_value(actual_field_set, 'Motor Mfg.'),
            'hp_frame': f"{get_field_value(design_field_set, 'HP')} / {get_field_value(design_field_set, 'Frame')}",
            'sf_code': f"{get_field_value(design_field_set, 'S.F.')} / {get_field_value(design_field_set, 'Code')}",
            'rpm_phase_hz': f"{get_field_value(design_field_set, 'RPM')} / {get_field_value(design_field_set, 'Phase')} / {get_field_value(design_field_set, 'HZ')}",
            'amps_design': get_field_value(design_field_set, 'Amps'),
            'amps_actual': get_field_value(actual_field_set, 'Amps'),
            'volts_design': get_field_value(design_field_set, 'Volts'),
            'volts_actual': get_field_value(actual_field_set, 'Volts'),
            'note': "",
        }

        notes = []
        note_count = 0
        data.append(equipment_data)
    return data

def fetch_velocity_data(equipment):
    design_field_set = equipment.form_fields["design"]
    actual_field_set = equipment.form_fields["actual"]

    equipment_data = {
        'fan_no': design_field_set.get('Fan No.', {}).get('value', ''),
        'design_cfm': design_field_set.get('Design C.F.M.', {}).get('value', ''),
        'duct_size': actual_field_set.get('Duct Size', {}).get('value', ''),
        'duct_area': actual_field_set.get('Duct Area', {}).get('value', ''),
        'reqd_vel': actual_field_set.get('Req. Vel', {}).get('value', ''),
        'traverse_location': actual_field_set.get('Traverse Location', {}).get('value', ''),
        'actual_cfm': {
            'initial': actual_field_set.get('Actual CFM. Initial', {}).get('value', ''),
            'final': actual_field_set.get('Actual CFM. Final', {}).get('value', ''),
        },
        'duct_static': {
            'initial': actual_field_set.get('Duct Static Initial', {}).get('value', ''),
            'final': actual_field_set.get('Duct Static Final', {}).get('value', ''),
        },
        'actual_vel': {
            'initial': actual_field_set.get('Actual Vel Initial', {}).get('value', ''),
            'final': actual_field_set.get('Actual Vel Final', {}).get('value', ''),
        },
        'note': "",
    }
    # Convert all values to upper case
    for key, val in equipment_data.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                equipment_data[key][sub_key] = str(sub_val).upper() if sub_val else ''
        else:
            equipment_data[key] = str(val).upper() if val else ''
    
    notes = []
    note_count = 0
    note_count = populate_notes_and_fields({
        'Note': 'note'
    }, design_field_set, actual_field_set, equipment_data, notes, note_count)
    equipment_data['note'] = " | ".join(notes)

    return equipment_data

def fetch_flow_measuring_data(equipments):
    data = []
    total_design_gpm = 0
    total_final_gpm = 0
    total_title = "TOTAL FLOW MEASURING STATION"
    for e in equipments:
        design_field_set = e.form_fields["design"]
        actual_field_set = e.form_fields["actual"]

        equipment_data = {
            'br_no': actual_field_set.get('Br No.', {}).get('value', ''),
            'fmf_no': actual_field_set.get('FMF No.', {}).get('value', ''),
            'location': actual_field_set.get('Location', {}).get('value', ''),
            'unit_number': e.code,
            'model_number': e.model_number,
            'design': {
                'set_pd': actual_field_set.get('Set / P.D.', {}).get('value', ''),
                'gpm': design_field_set.get('Design G.P.M.', {}).get('value', ''),
            },
            'initial_test': {
                'set_pd': actual_field_set.get('Initial Test Set / P.D.', {}).get('value', ''),
                'gpm': actual_field_set.get('Initial Test G.P.M.', {}).get('value', ''),
            },
            'final': {
                'set_pd': actual_field_set.get('Final Set / P.D.', {}).get('value', ''),
                'gpm': actual_field_set.get('Final G.P.M.', {}).get('value', ''),
            },
            'note': "",
        }
        # iterate and set '' for None
        for key, val in equipment_data.items():
            if isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    equipment_data[key][sub_key] = sub_val if sub_val else ''
            else:
                equipment_data[key] = val if val else ''

        notes = []
        note_count = 0
        note_count = populate_notes_and_fields({
            'Note': 'note'
        }, design_field_set, actual_field_set, equipment_data, notes, note_count)
        equipment_data['note'] = " | ".join(notes)

        data.append(equipment_data)
        total_design_gpm += int(equipment_data['design']['gpm']) if equipment_data['design']['gpm'] else 0
        total_final_gpm += int(equipment_data['final']['gpm']) if equipment_data['final']['gpm'] else 0
    return {
        'data': data, 
        'total_design_gpm': total_design_gpm, 
        'total_final_gpm': total_final_gpm, 
        'total_title': total_title
    }
