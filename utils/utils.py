import omitempty


def bool_from_str(text: str) -> bool:
    if text.lower() == 'true':
        return True
    if text.lower() == 'false':
        return False


class Serializer(object):
    @property
    def value(self):
        dict_values = omitempty(self.__dict__)
        if not dict_values:
            return None
        return self.__dict__
