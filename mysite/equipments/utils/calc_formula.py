import re

def calculate_formula(formula, fields, new_data, old_data, field_name, form_type):
    """
    Calculates the formula by replacing placeholders with actual values and ensures the result matches the validation regex.
    
    Parameters:
    - formula (str): The formula containing placeholders like '2_actual'.
    - fields (dict): A dictionary containing field information.
    - new_data (dict): New data to override existing values.
    - old_data (dict): Existing data which includes validation patterns.
    - field_name (str): The name of the field being calculated.
    
    Returns:
    - str or None: The calculated and validated result in the correct format, or None if validation fails.
    """
    
    # Extract the validation regex for the current field from old_data
    # Assuming old_data contains validation per field
    validation_regex = old_data.get('validation', "^([0-9]+(\\.[0-9]{1,2})?|\\*)$")
    
    print(f"Calculating formula for field: {field_name}")
    
    # Initialize value
    value = None
    
    # Find all placeholders in the formula
    placeholders = re.findall(r'\d+_[a-zA-Z]+', formula)
    
    for placeholder in placeholders:
        try:
            order, this_form_type = placeholder.split('_')
            order = int(order)
        except ValueError:
            print(f"Invalid placeholder format: {placeholder}")
            return None
        
        # Retrieve sub-fields based on this_form_type
        sub_fields = fields.get(this_form_type, {})
        matched_field_key = None
        for k, v in sub_fields.items():
            if v.get('order') == order:
                matched_field_key = k
                value = v.get('value')

                # Override with new_data if available
                if form_type == this_form_type:
                    new_value = new_data.get(matched_field_key).get('value', None)
                    value = new_value

                if (field_name == "B.H.P. (Calc.)") and (matched_field_key in ["Amperage", "Voltage"]) and ("-" in value):
                    value = v.get('value').split("-")
                    value = [float(v.strip()) for v in value]
                    v_actual = float(fields.get("actual", {}).get(matched_field_key, {}).get("value"))

                    diff = 10 ** 10
                    for v in value:
                        if abs(v - v_actual) < diff:
                            diff = abs(v - v_actual)
                            value = v

                break
        
        if matched_field_key is None:
            print(f"No matching field found for placeholder: {placeholder}")
            return None
        
        print(f"Value for placeholder {placeholder}: {value}")
        
        # If value is None or empty, cannot compute the formula
        if value is None or value == "":
            return None
        
        # Process the value based on its type and content
        if isinstance(value, str):
            if "@" in value:
                return None  # Invalid value
            if "-" in value:
                value = value.split("-")[0].strip()
            if "(" in value and ")" in value:
                # Remove parentheses
                value = value.replace("(", "").replace(")", "")
            if "*" not in value:
                try:
                    value = float(value)
                except ValueError:
                    print(f"Cannot convert value to float: {value}")
                    return None
        
        # Replace the placeholder in the formula with the actual value
        formula = formula.replace(placeholder, str(value))
        print(f"Updated formula: {formula}")
        
        # Early exit if formula contains invalid character
        if "@" in formula:
            return None
    
    try:
        # Evaluate the mathematical expression from the formula
        rs = eval(formula)
        rounded_result = rs
        if "}" in validation_regex:
            rounded_result = round(rs, int(validation_regex[validation_regex.index("}") - 1]))
        else:
            rounded_result = int(rs)
        print(f"Evaluated result: {rounded_result}")
    except Exception as e:
        print(f"Error evaluating formula: {e}")
        return None
    
    # Format the result appropriately for validation
    # Check if the validation regex expects parentheses
    if r"\(" in validation_regex and r"\)" in validation_regex:
        # Wrap the result in parentheses
        formatted_result = f"({rounded_result})"
    else:
        # No parentheses expected
        if isinstance(rounded_result, float) and rounded_result.is_integer():
            # Convert to integer if there's no fractional part
            rounded_result = int(rounded_result)
        formatted_result = str(rounded_result)
    
    # Convert the result to string for regex matching
    result_str = formatted_result
    
    print(f"Formatted result for validation: {result_str}")
    
    # Perform validation using the regex
    if re.match(validation_regex, result_str):
        return result_str
    else:
        print(f"Result does not match validation regex: {result_str}")
        return None


def calc_terminal_ak_factor(size):
    """
    Calculates the terminal AK factor based on the size.

    Valid size formats:
        20 * 14
        24 X 24 S
        (2) 17 X 9.5
        (2) 4 X 2 S
        250
    """
    calc_val = 0

    # Check if only one number (no spaces)
    if " " not in size:
        try:
            size_int = int(size)
            calc_val = (((size_int * 3.14) / 144) * 0.7)
            print(f"Calculated AK factor for single size {size}: {calc_val}")
            return round(calc_val, 2)
        except ValueError:
            print(f"Invalid size format (expected integer): {size}")
            return round(calc_val, 2)

    # Define a regex pattern to match the size formats
    pattern = r"^\s*(?:\((\d+)\)\s*)?(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)(?:\s*\w+)?\s*$"
    match = re.match(pattern, size)

    if match:
        # Extract the multiplier if present
        multiplier = match.group(1)
        num1 = match.group(2)
        num2 = match.group(3)

        try:
            num1 = float(num1)
            num2 = float(num2)
        except ValueError:
            print(f"Invalid numerical values in size: {size}")
            return round(calc_val, 2)

        if multiplier:
            try:
                multiplier = int(multiplier)
            except ValueError:
                print(f"Invalid multiplier in size: {size}")
                multiplier = 1  # Default to 1 if invalid

            # Apply the formula with multiplier
            calc_val = (((multiplier * (num1 * num2)) / 144) * 0.7)
            print(f"Calculated AK factor for size {size} with multiplier {multiplier}: {calc_val}")
        else:
            # Apply the formula without multiplier
            calc_val = (((num1 * num2) / 144) * 0.7)
            print(f"Calculated AK factor for size {size}: {calc_val}")

        return round(calc_val, 2)
    else:
        # Handle unexpected size formats
        print(f"Size format not recognized: {size}")
        return round(calc_val, 2)
