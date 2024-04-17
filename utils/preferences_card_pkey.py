class PreferencesCardsPKey:
    @staticmethod
    def generate_key(procedure_id, surgeon_id):
        """
        Generates a key by concatenating procedure_id and surgeon_id with '$$' as separator.

        :param procedure_id: The procedure ID.
        :param surgeon_id: The surgeon ID.
        :return: A concatenated key string.
        """
        return f'{procedure_id}$${surgeon_id}'

    @staticmethod
    def parse_key(key):
        """
        Parses the key into procedure_id and surgeon_id.

        :param key: The concatenated key string.
        :return: A tuple containing procedure_id and surgeon_id.
        """
        return key.split('$$', 1)


# Example usage
# key = PreferencesCardsPKey.generate_key("12345", "67890")
# procedure_id, surgeon_id = PreferencesCardsPKey.parse_key(key)
