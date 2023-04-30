# coding: utf-8

"""
    GreatMix Planner API

    The API for the Planner  # noqa: E501

    OpenAPI spec version: 1.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401



class CurrentProcedureModel(object):
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
        'side': 'str',
        'surgery_category': 'str',
        'surgery_name': 'str',
        'procedure': 'str',
        'surgery_duration': 'str',
        'procedure_code': 'str',
        'procedure_name': 'str',
        'procedure_icd': 'str'
    }

    attribute_map = {
        'side': 'side',
        'surgery_category': 'surgery_category',
        'surgery_name': 'surgery_name',
        'procedure': 'procedure',
        'surgery_duration': 'surgery_duration',
        'procedure_code': 'procedure_code',
        'procedure_name': 'procedure_name',
        'procedure_icd': 'procedure_icd'
    }

    def __init__(self, side=None, surgery_category=None, surgery_name=None, procedure=None, surgery_duration=None, procedure_code=None, procedure_name=None, procedure_icd=None):  # noqa: E501
        """CurrentProcedureModel - a model defined in Swagger"""  # noqa: E501
        self._side = None
        self._surgery_category = None
        self._surgery_name = None
        self._procedure = None
        self._surgery_duration = None
        self._procedure_code = None
        self._procedure_name = None
        self._procedure_icd = None
        self.discriminator = None
        if side is not None:
            self.side = side
        if surgery_category is not None:
            self.surgery_category = surgery_category
        if surgery_name is not None:
            self.surgery_name = surgery_name
        if procedure is not None:
            self.procedure = procedure
        if surgery_duration is not None:
            self.surgery_duration = surgery_duration
        if procedure_code is not None:
            self.procedure_code = procedure_code
        if procedure_name is not None:
            self.procedure_name = procedure_name
        if procedure_icd is not None:
            self.procedure_icd = procedure_icd

    @property
    def side(self):
        """Gets the side of this CurrentProcedureModel.  # noqa: E501


        :return: The side of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._side

    @side.setter
    def side(self, side):
        """Sets the side of this CurrentProcedureModel.


        :param side: The side of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._side = side

    @property
    def surgery_category(self):
        """Gets the surgery_category of this CurrentProcedureModel.  # noqa: E501


        :return: The surgery_category of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._surgery_category

    @surgery_category.setter
    def surgery_category(self, surgery_category):
        """Sets the surgery_category of this CurrentProcedureModel.


        :param surgery_category: The surgery_category of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._surgery_category = surgery_category

    @property
    def surgery_name(self):
        """Gets the surgery_name of this CurrentProcedureModel.  # noqa: E501


        :return: The surgery_name of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._surgery_name

    @surgery_name.setter
    def surgery_name(self, surgery_name):
        """Sets the surgery_name of this CurrentProcedureModel.


        :param surgery_name: The surgery_name of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._surgery_name = surgery_name

    @property
    def procedure(self):
        """Gets the procedure of this CurrentProcedureModel.  # noqa: E501


        :return: The procedure of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._procedure

    @procedure.setter
    def procedure(self, procedure):
        """Sets the procedure of this CurrentProcedureModel.


        :param procedure: The procedure of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._procedure = procedure

    @property
    def surgery_duration(self):
        """Gets the surgery_duration of this CurrentProcedureModel.  # noqa: E501


        :return: The surgery_duration of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._surgery_duration

    @surgery_duration.setter
    def surgery_duration(self, surgery_duration):
        """Sets the surgery_duration of this CurrentProcedureModel.


        :param surgery_duration: The surgery_duration of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._surgery_duration = surgery_duration

    @property
    def procedure_code(self):
        """Gets the procedure_code of this CurrentProcedureModel.  # noqa: E501


        :return: The procedure_code of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._procedure_code

    @procedure_code.setter
    def procedure_code(self, procedure_code):
        """Sets the procedure_code of this CurrentProcedureModel.


        :param procedure_code: The procedure_code of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._procedure_code = procedure_code

    @property
    def procedure_name(self):
        """Gets the procedure_name of this CurrentProcedureModel.  # noqa: E501


        :return: The procedure_name of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._procedure_name

    @procedure_name.setter
    def procedure_name(self, procedure_name):
        """Sets the procedure_name of this CurrentProcedureModel.


        :param procedure_name: The procedure_name of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._procedure_name = procedure_name

    @property
    def procedure_icd(self):
        """Gets the procedure_icd of this CurrentProcedureModel.  # noqa: E501


        :return: The procedure_icd of this CurrentProcedureModel.  # noqa: E501
        :rtype: str
        """
        return self._procedure_icd

    @procedure_icd.setter
    def procedure_icd(self, procedure_icd):
        """Sets the procedure_icd of this CurrentProcedureModel.


        :param procedure_icd: The procedure_icd of this CurrentProcedureModel.  # noqa: E501
        :type: str
        """

        self._procedure_icd = procedure_icd

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
        if issubclass(CurrentProcedureModel, dict):
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
        if not isinstance(other, CurrentProcedureModel):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
