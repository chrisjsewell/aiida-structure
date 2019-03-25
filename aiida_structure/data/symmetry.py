import copy
import json
import os
import tempfile

import jsonschema
from jsonschema import ValidationError as SchemeError
import numpy as np

from aiida.common.utils import classproperty
from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Data

from aiida_structure.schema import SCHEMAPATH


class SymmetryData(Data):
    """
    Stores data regarding the symmetry of a structure

    - symmetry operations are stored on file (in the style of ArrayData)
    - the rest of the values (and the number of symmetry operators)
      are stored as attributes in the database

    """
    _ops_filename = "operations.npy"

    @classproperty
    def data_schema(cls):
        with open(os.path.join(SCHEMAPATH, "symmetry.json")) as fobj:
            schema = json.load(fobj)
        return schema

    def _validate(self):
        super(SymmetryData, self)._validate()

        fname = self._ops_filename
        if fname not in self.get_folder_list():
            raise ValidationError("operations not set")

        try:
            jsonschema.validate(self.data, self.data_schema)
        except SchemeError as err:
            raise ValidationError(err)

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

        # store all but the symmetry operations as attributes
        old_dict = copy.deepcopy(dict(self.iterattrs()))
        attributes_set = False
        try:
            # Delete existing attributes
            self._del_all_attrs()
            # I set the keys
            self._update_attrs(
                {k: v
                 for k, v in data.items() if k != "operations"})
            self._set_attr("num_symops", len(data["operations"]))
            attributes_set = True
        finally:
            if not attributes_set:
                try:
                    # Try to restore the old data
                    self._del_all_attrs()
                    self._update_attrs(old_dict)
                except ModificationNotAllowed:
                    pass

        # store the symmetry operations on file
        self._set_operations(data["operations"])

    def _update_attrs(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.iteritems():
            self._set_attr(k, v)

    def _set_operations(self, ops):
        fname = self._ops_filename

        if fname in self.get_folder_list():
            self.remove_path(fname)

        with tempfile.NamedTemporaryFile() as f:
            # Store in a temporary file, and then add to the node
            np.save(f, ops)
            f.flush(
            )  # Important to flush here, otherwise the next copy command
            # will just copy an empty file
            super(SymmetryData, self).add_path(f.name, fname)

    def _get_operations(self):
        fname = self._ops_filename
        if fname not in self.get_folder_list():
            raise KeyError("symmetry operations not set for node pk={}".format(
                self.pk))

        array = np.load(self.get_abs_path(fname))

        return array.tolist()

    @property
    def data(self):
        """
        Return the data as an AttributeDict
        """
        data = dict(self.iterattrs())
        if "num_symops" in data:
            data.pop("num_symops")
        data["operations"] = self._get_operations()
        return AttributeDict(data)

    @property
    def num_symops(self):
        return self.get_attr("num_symops", None)

    @property
    def space_group(self):
        return self.get_attr("space_group", None)

    def add_path(self, src_abs, dst_path):
        from aiida.common.exceptions import ModificationNotAllowed

        raise ModificationNotAllowed(
            "Cannot add files or directories to StructSettingsData object")

    def compare_operations(self, ops, decimal=5):
        """compare operations against stored ones

        :param ops: list of (flattened) symmetry operations
        :param decimal: number of decimal points to round values to
        :returns: dict of differences
        """
        ops_orig = self._get_operations()

        # create a set for each
        ops_orig = set(
            [tuple([round(i, decimal) for i in op]) for op in ops_orig])
        ops_new = set([tuple([round(i, decimal) for i in op]) for op in ops])

        differences = {}
        if ops_orig.difference(ops_new):
            differences["missing"] = ops_orig.difference(ops_new)
        if ops_new.difference(ops_orig):
            differences["additional"] = ops_new.difference(ops_orig)

        return differences
