# coding: utf-8

"""
    GreatMix Planner API

    The API for the Planner  # noqa: E501

    OpenAPI spec version: 1.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401


class RequestSchema(object):
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
        'tasks': 'list[Task]',
        'blocks': 'list[Block]',
        'metadata': 'list[Metadata]'
    }

    attribute_map = {
        'tasks': 'tasks',
        'blocks': 'blocks',
        'metadata': 'metadata'
    }

    def __init__(self, tasks=None, blocks=None, metadata=None):  # noqa: E501
        """RequestSchema - a model defined in Swagger"""  # noqa: E501
        self._tasks = None
        self._blocks = None
        self._metadata = None
        self.discriminator = None
        if tasks is not None:
            self.tasks = tasks
        if blocks is not None:
            self.blocks = blocks
        if metadata is not None:
            self.metadata = metadata

    @property
    def tasks(self):
        """Gets the tasks of this RequestSchema.  # noqa: E501


        :return: The tasks of this RequestSchema.  # noqa: E501
        :rtype: list[Task]
        """
        return self._tasks

    @tasks.setter
    def tasks(self, tasks):
        """Sets the tasks of this RequestSchema.


        :param tasks: The tasks of this RequestSchema.  # noqa: E501
        :type: list[Task]
        """

        self._tasks = tasks

    @property
    def blocks(self):
        """Gets the blocks of this RequestSchema.  # noqa: E501


        :return: The blocks of this RequestSchema.  # noqa: E501
        :rtype: list[Block]
        """
        return self._blocks

    @blocks.setter
    def blocks(self, blocks):
        """Sets the blocks of this RequestSchema.


        :param blocks: The blocks of this RequestSchema.  # noqa: E501
        :type: list[Block]
        """

        self._blocks = blocks

    @property
    def metadata(self):
        """Gets the metadata of this RequestSchema.  # noqa: E501


        :return: The metadata of this RequestSchema.  # noqa: E501
        :rtype: list[Metadata]
        """
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        """Sets the metadata of this RequestSchema.


        :param metadata: The metadata of this RequestSchema.  # noqa: E501
        :type: list[Metadata]
        """

        self._metadata = metadata

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
        if issubclass(RequestSchema, dict):
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
        if not isinstance(other, RequestSchema):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
