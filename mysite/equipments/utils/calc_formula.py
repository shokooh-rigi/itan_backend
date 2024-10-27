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


import re
import logging
import operator
from typing import Union, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def evaluate_formula_with_validation(
        formula: str,
        field_definitions: Dict[str, dict],
        current_form_data: Dict[str, dict],
        previous_form_data: Dict[str, dict],
        field_name: str,
        form_type: str
) -> Optional[str]:
    """
    Evaluate the formula by substituting variables and validating the final result.

    Parameters:
    - formula (str): The formula containing variables and calculations.
    - field_definitions (dict): Definitions of the fields in the form.
    - current_form_data (dict): New data being updated.
    - previous_form_data (dict): Previous form data, including validation patterns.
    - field_name (str): The name of the field for which the formula is computed.
    - form_type (str): The type of form that determines which form is used.

    Returns:
    - str or None: The computed and validated result, or None if validation fails.
    """

    # Get the validation pattern from previous data
    validation_pattern = previous_form_data.get('validation', "^([0-9]+(\\.[0-9]{1,2})?|\\*)$")

    logger.debug(f"Calculating formula for field: {field_name}")

    value_placeholder = None
    found_placeholders = re.findall(r'\d+_[a-zA-Z]+', formula)

    for placeholder in found_placeholders:
        try:
            order_index, placeholder_form_type = placeholder.split('_')
            order_index = int(order_index)
        except ValueError:
            logger.error(f"Invalid placeholder format: {placeholder}")
            return None

        # Extract fields related to the form type
        form_fields = field_definitions.get(placeholder_form_type, {})
        matched_field_key = None

        # Search for the field that matches the order_index
        for field_key, field_info in form_fields.items():
            if field_info.get('order') == order_index:
                matched_field_key = field_key
                field_value = field_info.get('value')

                if form_type == placeholder_form_type:
                    new_value = current_form_data.get(matched_field_key, {}).get('value', None)
                    field_value = new_value if new_value is not None else field_value

                # If the field name is specific, adjust the value accordingly
                if (field_name == "B.H.P. (Calc.)") and (matched_field_key in ["Amperage", "Voltage"]) and (
                        "-" in field_value):
                    field_value = [float(val.strip()) for val in field_info.get('value').split("-")]
                    actual_value = float(field_definitions.get("actual", {}).get(matched_field_key, {}).get("value"))
                    field_value = min(field_value, key=lambda x: abs(x - actual_value))

                break

        if matched_field_key is None:
            logger.error(f"No matching field found for placeholder: {placeholder}")
            return None

        logger.debug(f"Value for placeholder {placeholder}: {field_value}")

        if field_value is None or field_value == "":
            return None

        # Check format and type of the field value
        if isinstance(field_value, str):
            if "@" in field_value:
                return None  # Invalid value
            if "-" in field_value:
                field_value = field_value.split("-")[0].strip()
            if "(" in field_value and ")" in field_value:
                field_value = field_value.replace("(", "").replace(")", "")
            if "*" not in field_value:
                try:
                    field_value = float(field_value)
                except ValueError:
                    logger.error(f"Cannot convert value to float: {field_value}")
                    return None

        # Replace placeholder with actual value
        formula = formula.replace(placeholder, str(field_value))
        logger.debug(f"Updated formula: {formula}")

        if "@" in formula:
            return None

    try:
        # Safely evaluate mathematical expression without using eval
        calculated_result = safely_evaluate_formula(formula)
        logger.debug(f"Evaluated result: {calculated_result}")
    except Exception as e:
        logger.error(f"Error evaluating formula: {e}")
        return None

    formatted_result = format_result_for_validation(calculated_result, validation_pattern)
    logger.debug(f"Formatted result for validation: {formatted_result}")

    if re.match(validation_pattern, formatted_result):
        return formatted_result
    else:
        logger.error(f"Result does not match validation pattern: {formatted_result}")
        return None


def safely_evaluate_formula(formula: str) -> float:
    """
    Evaluate the formula safely using valid operators.

    Parameters:
    - formula (str): The formula to be evaluated.

    Returns:
    - float: The result of the formula evaluation.

    Raises:
    - ValueError: If an unsupported operator is found.
    """
    allowed_operations = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
    }

    tokens = re.split(r'(\D)', formula)
    result = float(tokens[0])

    for i in range(1, len(tokens), 2):
        operation = tokens[i]
        number = float(tokens[i + 1])
        if operation in allowed_operations:
            result = allowed_operations[operation](result, number)
        else:
            raise ValueError(f"Unsupported operator {operation} in formula")

    return result


def format_result_for_validation(result: float, validation_pattern: str) -> str:
    """
    Format the result to match the validation pattern.

    Parameters:
    - result (float): The computed result.
    - validation_pattern (str): The validation pattern to match.

    Returns:
    - str: The formatted result.
    """
    if r"\(" in validation_pattern and r"\)" in validation_pattern:
        return f"({result})"
    else:
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 2))


def calculate_terminal_air_flow_factor(size: str) -> float:
    """
    Calculate the air flow factor based on the input size.

    Parameters:
    - size (str): A string containing the size for calculating air flow factor.

    Returns:
    - float: The computed air flow factor.

    Valid formats:
        20 * 14
        24 X 24 S
        (2) 17 X 9.5
        (2) 4 X 2 S
        250
    """
    air_flow_factor = 0

    if " " not in size:
        try:
            size_as_int = int(size)
            air_flow_factor = (((size_as_int * 3.14) / 144) * 0.7)
            logger.debug(f"Calculated air flow factor for single size {size}: {air_flow_factor}")
            return round(air_flow_factor, 2)
        except ValueError:
            logger.error(f"Invalid size format (expected integer): {size}")
            return round(air_flow_factor, 2)

    size_pattern = r"^\s*(?:\((\d+)\)\s*)?(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)(?:\s*\w+)?\s*$"
    match = re.match(size_pattern, size)

    if match:
        multiplier = match.group(1)
        dimension_1 = float(match.group(2))
        dimension_2 = float(match.group(3))

        multiplier = int(multiplier) if multiplier else 1
        air_flow_factor = (((multiplier * (dimension_1 * dimension_2)) / 144) * 0.7)
        logger.debug(f"Calculated air flow factor for size {size} with multiplier {multiplier}: {air_flow_factor}")
        return round(air_flow_factor, 2)
    else:
        logger.error(f"Size format not recognized: {size}")
        return round(air_flow_factor, 2)
