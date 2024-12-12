from django.urls import reverse

from mysite.dbmanagement.models import EquipmentManufacturer
from mysite.equipments.models import Equipment, TestSheet
from mysite.sheetcreator.models import DataSheet, Sheet


class OrderFullUpdateService:
    """
    A service class to handle the business logic related to orders,
    such as fetching order details, processing equipment, and generating URLs.
    """

    def __init__(self, order):
        """
        Initializes the OrderService with the given order.

        Args:
            order (Order): The order instance for which details need to be fetched.
        """
        self.order = order

    def get_order_details(self):
        """
        Fetches and processes the details of the order, including equipment, test sheets,
        manufacturers, and more. Returns the processed order details in a dictionary.

        Returns:
            dict: A dictionary containing processed order details.
        """
        data_sheets = self.order.datasheet_set.all()
        sheets = self.order.sheet_set.all()
        equipment_types = Equipment.objects.all()
        manufacturers = EquipmentManufacturer.objects.all()
        modules_type = "Equipments"

        # Process equipment types for the response
        equipment_type_details = [
            {
                'id': equipment.id,
                'name': equipment.name,
                'test_sheet': equipment.test_sheet.name if equipment.test_sheet else None,
                'test_sheet_id': equipment.test_sheet.id if equipment.test_sheet else None,
            }
            for equipment in equipment_types
        ]

        # Process test sheets for the response
        test_sheets = [
            {
                'id': test_sheet.id,
                'name': test_sheet.name,
            }
            for test_sheet in TestSheet.objects.all()
        ]

        # Process the equipment information from the data sheets and sheets
        equipments = self._get_equipment_details(data_sheets, sheets)

        # Return the processed order details
        return {
            "order": self.order,
            "equipments": equipments,
            "equipment_types": equipment_type_details,
            "test_sheets": test_sheets,
            "modules_type": modules_type,
            "manufacturers": manufacturers,
        }

    def _get_equipment_details(self, data_sheets, sheets):
        """
        Processes and aggregates equipment details from both data sheets and sheets.

        Args:
            data_sheets (QuerySet): The data sheets related to the order.
            sheets (QuerySet): The sheets related to the order.

        Returns:
            list: A list of dictionaries containing processed equipment details.
        """
        equipment_dict = {}

        air_terminal = self._get_air_terminal_from_data_sheets(data_sheets)

        # Process equipment from data sheets
        for data_sheet in data_sheets:
            self._process_data_sheet_equipment(data_sheet, equipment_dict, air_terminal)

        # Process equipment from sheets
        for sheet in sheets:
            self._process_sheet_equipment(sheet, equipment_dict)

        # Return sorted equipment details
        return self._sort_equipment_by_service(list(equipment_dict.values()))

    def _get_air_terminal_from_data_sheets(self, data_sheets):
        """
        Retrieves the air terminal ID from the data sheets.

        Args:
            data_sheets (QuerySet): The data sheets related to the order.

        Returns:
            int or None: The air terminal ID if found, else None.
        """
        air_terminal_data_sheet = DataSheet.objects.filter(
            project=self.order, test_sheet_type__name__icontains='terminal'
        ).first()

        return air_terminal_data_sheet.id if air_terminal_data_sheet else None

    def _process_data_sheet_equipment(self, data_sheet, equipment_dict, air_terminal):
        """
        Processes and aggregates equipment details from a single data sheet.

        Args:
            data_sheet (DataSheet): The data sheet to process.
            equipment_dict (dict): A dictionary to store aggregated equipment details.
            air_terminal (int): The air terminal ID if found.
        """
        equipment_items = data_sheet.datasheetequipment_set.all()
        for equipment in equipment_items:
            key = (equipment.equipment_type.id, equipment.sheet.test_sheet_type.id)
            if key in equipment_dict:
                equipment_dict[key]['quantity'] += 1
                equipment_dict[key]['quantity_range'] = range(equipment_dict[key]['quantity'])
                equipment_dict[key]['equipments'].append(equipment)
            else:
                equipment_dict[key] = self._create_equipment_dict(equipment, air_terminal, 'datasheetequipment')

            self._set_urls_and_colours_for_equipment(equipment, equipment_dict, key)

    def _process_sheet_equipment(self, sheet, equipment_dict):
        """
        Processes and aggregates equipment details from a single sheet.

        Args:
            sheet (Sheet): The sheet to process.
            equipment_dict (dict): A dictionary to store aggregated equipment details.
        """
        equipment_items = sheet.sheetequipment_set.all()
        for equipment in equipment_items:
            key = (equipment.equipment_type.id, equipment.sheet.test_sheet_type.id)
            if key in equipment_dict:
                equipment_dict[key]['quantity'] += 1
                equipment_dict[key]['quantity_range'] = range(equipment_dict[key]['quantity'])
                equipment_dict[key]['equipments'].append(equipment)
            else:
                equipment_dict[key] = self._create_equipment_dict(equipment, None, 'sheetequipment')

            self._set_urls_and_colours_for_equipment(equipment, equipment_dict, key)

    def _create_equipment_dict(self, equipment, air_terminal, equipment_type):
        """
        Creates a dictionary to store the details of an equipment.

        Args:
            equipment (Equipment): The equipment instance to store details for.
            air_terminal (int or None): The air terminal ID.
            equipment_type (str): The type of equipment ('datasheetequipment' or 'sheetequipment').

        Returns:
            dict: A dictionary containing equipment details.
        """
        return {
            'id': equipment.id,
            'equipment': equipment.equipment_type.name,
            'equipment_id': equipment.equipment_type.id,
            'sheet': equipment.sheet,
            'test_sheet': equipment.sheet.test_sheet_type.name,
            'test_sheet_id': equipment.sheet.test_sheet_type.id,
            'air_terminal_data_sheet': air_terminal,
            'service': equipment.equipment.equipment_type.service.name,
            'equipments': [equipment],
            'quantity': 1,
            'quantity_range': range(1),
            'type': equipment_type,
            'general_url': None,
            'design_url': None,
            'actual_url': None,
            'general_colour': None,
            'design_colour': None,
            'actual_colour': None,
        }

    def _set_urls_and_colours_for_equipment(self, equipment, equipment_dict, key):
        """
        Sets the URLs and colour flags for a piece of equipment based on its status.

        Args:
            equipment (Equipment): The equipment instance to process.
            equipment_dict (dict): A dictionary to store the equipment details.
            key (tuple): The key used to store the equipment in the dictionary.
        """
        if equipment.sheet.test_sheet_type.name.lower() == "air moving":
            if not equipment.equipment.main_data_entry_confirmed:
                equipment_dict[key]['general_url'] = reverse('sheetEquipmentCommonData', args=[equipment.id])
            else:
                equipment_dict[key]['general_url'] = reverse('sheetEquipmentCommonDataEdit', args=[equipment.id])

            equipment_dict[key]['design_url'] = reverse('sheetEquipmentDesignValue', args=[equipment.id])
            if not equipment.equipment.actual_data_entry_confirmed:
                equipment_dict[key]['actual_url'] = reverse('sheetEquipmentActualValue', args=[equipment.id])
            else:
                equipment_dict[key]['actual_url'] = reverse('sheetEquipmentActualValueEdit', args=[equipment.id])
        else:
            equipment_dict[key]['general_url'] = reverse('vavSheetEquipmentGeneralData', args=[equipment.id])
            equipment_dict[key]['design_url'] = reverse('vavSheetEquipmentDesignData', args=[equipment.id])
            equipment_dict[key]['actual_url'] = reverse('vavSheetEquipmentActualData', args=[equipment.id])

        self._set_colour_flags_for_equipment(equipment, equipment_dict, key)

    def _set_colour_flags_for_equipment(self, equipment, equipment_dict, key):
        """
        Sets the colour flags for a piece of equipment based on its data entry confirmation status.

        Args:
            equipment (Equipment): The equipment instance to process.
            equipment_dict (dict): A dictionary to store the equipment details.
            key (tuple): The key used to store the equipment in the dictionary.
        """
        if equipment.equipment.main_data_entry_confirmed:
            equipment_dict[key]['general_colour'] = '#008000'
        if equipment.equipment.design_data_entry_confirmed:
            equipment_dict[key]['design_colour'] = '#008000'
        if equipment.equipment.actual_data_entry_confirmed:
            equipment_dict[key]['actual_colour'] = '#008000'

    def _sort_equipment_by_service(self, equipment_list):
        """
        Sorts the equipment list by their service type, prioritizing 'Air Balancing' and 'Water Balancing'.

        Args:
            equipment_list (list): A list of equipment dictionaries to sort.

        Returns:
            list: A sorted list of equipment dictionaries.
        """
        sorted_equipment = []

        # Prioritize 'Air Balancing' equipment
        for equipment in equipment_list:
            if 'Air Balancing' == equipment['service']:
                sorted_equipment.append(equipment)

        # Prioritize 'Water Balancing' equipment
        for equipment in equipment_list:
            if 'Water Balancing' == equipment['service']:
                sorted_equipment.append(equipment)

        # Append all remaining equipment
        for equipment in equipment_list:
            if equipment not in sorted_equipment:
                sorted_equipment.append(equipment)

        return sorted_equipment
