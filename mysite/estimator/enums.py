from enum import Enum


class ControlSystemChoices(Enum):
    ZERO = 0, '0'
    ONE_PERCENT = 1, '1%'
    TWO_PERCENT = 2, '2%'
    THREE_PERCENT = 3, '3%'
    FOUR_PERCENT = 4, '4%'
    FIVE_PERCENT = 5, '5%'


class HoursChoices(Enum):
    REGULAR_HOURS = 0, 'Regular Hours'
    OFF_HOURS = 5, 'Off Hours'
    SATURDAY_HOLIDAYS = 10, 'Saturday/Holidays'
    SUNDAY = 15, 'Sunday'
