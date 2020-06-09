from typing import List


class Final:
    def __init__(self, final_properties: List[str] = None):
        """
        Makes all or specific properties of class final.

        These properties can be assigned once.

        :param final_properties: list of final properties
        """

        self.__dict__['__final_properties'] = final_properties

    def __setattr__(self, key, value) -> None:
        final_properties = self.__dict__.get('__final_properties', None)
        if final_properties:
            if key in final_properties:
                message = 'Property %s of %s is final.It can be assigned once.' % (key, self.__class__.__name__)
                self.__set_and_lock(key, value, message)
            else:
                self.__dict__[key] = value
        else:
            message = 'All properties of %s are final.They can be assigned once.' % self.__class__.__name__
            self.__set_and_lock(key, value, message)

    def __set_and_lock(self, key, value, message):
        locked = '__%s_locked' % key
        if self.__dict__.get(locked, False):
            raise AttributeError(message)
        else:
            self.__dict__[key] = value
            self.__dict__[locked] = True
