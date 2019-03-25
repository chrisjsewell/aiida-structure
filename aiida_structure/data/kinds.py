import copy
import json
import os

import jsonschema
from jsonschema import ValidationError as SchemeError

from aiida.common.utils import classproperty
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Data

from aiida_structure.schema import SCHEMAPATH


class KindData(Data):
    """stores additional data for StructureData Kinds"""
    @classproperty
    def data_schema(cls):
        with open(os.path.join(SCHEMAPATH, "kinds.json")) as fobj:
            schema = json.load(fobj)
        return schema

    def _validate(self):
        super(KindData, self)._validate()

        try:
            jsonschema.validate(self.data, self.data_schema)
        except SchemeError as err:
            raise ValidationError(err)

        kinds = self.data["kind_names"]
        for key, value in self.data.items():
            if len(value) != len(kinds):
                raise ValidationError(
                    "'{}' array not the same length as 'kind_names'"
                    "".format(key))

    def set_data(self, data):
        """
        Replace the current data with another one.

        :param data: The dictionary to set.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        # first validate the inputs
        try:
            jsonschema.validate(data, self.data_schema)
        except SchemeError as err:
            raise ValidationError(err)

        kinds = data["kind_names"]
        for key, value in data.items():
            if len(value) != len(kinds):
                raise ValidationError(
                    "'{}' array not the same length as 'kind_names'"
                    "".format(key))

        # store all but the symmetry operations as attributes
        old_dict = copy.deepcopy(dict(self.iterattrs()))
        attributes_set = False
        try:
            # Delete existing attributes
            self._del_all_attrs()
            # I set the keys
            self._update_attrs(data)
            attributes_set = True
        finally:
            if not attributes_set:
                try:
                    # Try to restore the old data
                    self._del_all_attrs()
                    self._update_attrs(old_dict)
                except ModificationNotAllowed:
                    pass

    def _update_attrs(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.iteritems():
            self._set_attr(k, v)

    @property
    def data(self):
        """
        Return the data as an AttributeDict
        """
        data = dict(self.iterattrs())
        return AttributeDict(data)

    @property
    def kind_dict(self):
        """
        Return an AttributeDict with nested keys <kind_name>.<field> = value
        """
        data = dict(self.iterattrs())
        kind_names = data.pop("kind_names")
        dct = {k: {} for k in kind_names}
        for key, values in data.items():
            for kind, value in zip(kind_names, values):
                dct[kind][key] = value
        return AttributeDict(dct)

    @property
    def field_dict(self):
        """
        Return an AttributeDict with nested keys <field>.<kind_name> = value
        """
        data = dict(self.iterattrs())
        kind_names = data.pop("kind_names")
        dct = {}
        for key, values in data.items():
            dct[key] = {}
            for kind, value in zip(kind_names, values):
                dct[key][kind] = value
        return AttributeDict(dct)
