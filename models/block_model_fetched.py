# coding: utf-8

"""
    GreatMix Planner API

    The API for the Planner  # noqa: E501

    OpenAPI spec version: 1.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401



from models.time_model import TimeModel


class BlockModelFetched(TimeModel):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'id': 'int',
        'title': 'str',
        'nurse_name': 'str',
        'sanitaire_name': 'str',
        'assistant_name': 'str',
        'anesthetist_name': 'str',
        'doctor_name': 'str',
        'doctor_id': 'int',
        'doctors_license': 'str'
    }

    attribute_map = {
        'id': 'id',
        'title': 'title',
        'nurse_name': 'nurse_name',
        'sanitaire_name': 'sanitaire_name',
        'assistant_name': 'assistant_name',
        'anesthetist_name': 'anesthetist_name',
        'doctor_name': 'doctor_name',
        'doctor_id': 'doctor_id',
        'doctors_license': 'doctors_license'
    }

    def __init__(self, start=None, end=None, resourceId=None, room_id=None, id=None, title=None, nurse_name=None, sanitaire_name=None, assistant_name=None, anesthetist_name=None, doctor_name=None, doctor_id=None, doctors_license=None):  # noqa: E501
        super().__init__(id, start, end, resourceId, room_id)
        """BlockModelFetched - a model defined in Swagger"""  # noqa: E501
        self._id = None
        self._title = None
        self._nurse_name = None
        self._sanitaire_name = None
        self._assistant_name = None
        self._anesthetist_name = None
        self._doctor_name = None
        self._doctor_id = None
        self._doctors_license = None
        self.discriminator = None
        if id is not None:
            self.id = id
        if title is not None:
            self.title = title
        if nurse_name is not None:
            self.nurse_name = nurse_name
        if sanitaire_name is not None:
            self.sanitaire_name = sanitaire_name
        if assistant_name is not None:
            self.assistant_name = assistant_name
        if anesthetist_name is not None:
            self.anesthetist_name = anesthetist_name
        if doctor_name is not None:
            self.doctor_name = doctor_name
        if doctor_id is not None:
            self.doctor_id = doctor_id
        if doctors_license is not None:
            self.doctors_license = doctors_license

    @property
    def id(self):
        """Gets the id of this BlockModelFetched.  # noqa: E501


        :return: The id of this BlockModelFetched.  # noqa: E501
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this BlockModelFetched.


        :param id: The id of this BlockModelFetched.  # noqa: E501
        :type: int
        """

        self._id = id

    @property
    def title(self):
        """Gets the title of this BlockModelFetched.  # noqa: E501


        :return: The title of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this BlockModelFetched.


        :param title: The title of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._title = title

    @property
    def nurse_name(self):
        """Gets the nurse_name of this BlockModelFetched.  # noqa: E501


        :return: The nurse_name of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._nurse_name

    @nurse_name.setter
    def nurse_name(self, nurse_name):
        """Sets the nurse_name of this BlockModelFetched.


        :param nurse_name: The nurse_name of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._nurse_name = nurse_name

    @property
    def sanitaire_name(self):
        """Gets the sanitaire_name of this BlockModelFetched.  # noqa: E501


        :return: The sanitaire_name of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._sanitaire_name

    @sanitaire_name.setter
    def sanitaire_name(self, sanitaire_name):
        """Sets the sanitaire_name of this BlockModelFetched.


        :param sanitaire_name: The sanitaire_name of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._sanitaire_name = sanitaire_name

    @property
    def assistant_name(self):
        """Gets the assistant_name of this BlockModelFetched.  # noqa: E501


        :return: The assistant_name of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._assistant_name

    @assistant_name.setter
    def assistant_name(self, assistant_name):
        """Sets the assistant_name of this BlockModelFetched.


        :param assistant_name: The assistant_name of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._assistant_name = assistant_name

    @property
    def anesthetist_name(self):
        """Gets the anesthetist_name of this BlockModelFetched.  # noqa: E501


        :return: The anesthetist_name of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._anesthetist_name

    @anesthetist_name.setter
    def anesthetist_name(self, anesthetist_name):
        """Sets the anesthetist_name of this BlockModelFetched.


        :param anesthetist_name: The anesthetist_name of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._anesthetist_name = anesthetist_name

    @property
    def doctor_name(self):
        """Gets the doctor_name of this BlockModelFetched.  # noqa: E501


        :return: The doctor_name of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._doctor_name

    @doctor_name.setter
    def doctor_name(self, doctor_name):
        """Sets the doctor_name of this BlockModelFetched.


        :param doctor_name: The doctor_name of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._doctor_name = doctor_name

    @property
    def doctor_id(self):
        """Gets the doctor_id of this BlockModelFetched.  # noqa: E501


        :return: The doctor_id of this BlockModelFetched.  # noqa: E501
        :rtype: int
        """
        return self._doctor_id

    @doctor_id.setter
    def doctor_id(self, doctor_id):
        """Sets the doctor_id of this BlockModelFetched.


        :param doctor_id: The doctor_id of this BlockModelFetched.  # noqa: E501
        :type: int
        """

        self._doctor_id = doctor_id

    @property
    def doctors_license(self):
        """Gets the doctors_license of this BlockModelFetched.  # noqa: E501


        :return: The doctors_license of this BlockModelFetched.  # noqa: E501
        :rtype: str
        """
        return self._doctors_license

    @doctors_license.setter
    def doctors_license(self, doctors_license):
        """Sets the doctors_license of this BlockModelFetched.


        :param doctors_license: The doctors_license of this BlockModelFetched.  # noqa: E501
        :type: str
        """

        self._doctors_license = doctors_license

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in self.swagger_types.items():
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(BlockModelFetched, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, BlockModelFetched):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
