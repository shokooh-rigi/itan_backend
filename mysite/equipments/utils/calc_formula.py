import re


def calculate_formula(formula, fields, new_data):
    # Regex to identify placeholders like '2_actual'
    value = None
    placeholders = re.findall(r'\d+_[a-zA-Z]+', formula)
    for placeholder in placeholders:
        order, form_type = placeholder.split('_')

        sub_fields = fields.get(form_type, {})
        for k, v in sub_fields.items():
            if v.get('order') == int(order):
                value = v.get('value')
                break
        # check if the value key is in the new data
        new_value = new_data.get(k)
        if new_value:
            value = new_value
        if value is None:
            return None  # if any value is None, we cannot compute the formula
        # Replace placeholder in formula with the actual value
        formula = formula.replace(placeholder, str(value))
        if "@" in formula:
            return None
    try:
        # Evaluate the mathematical expression from the formula
        rs = eval(formula)
        return round(rs, 2)
    except Exception as e:
        print(f"Error evaluating formula: {e}")
        return None
