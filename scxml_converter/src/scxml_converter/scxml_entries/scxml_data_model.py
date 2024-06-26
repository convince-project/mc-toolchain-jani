# Copyright (c) 2024 - for information on the respective copyright owner
# see the NOTICE file

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Container for the variables defined in the SCXML model. In XML, it has the tag `datamodel`.
"""

from typing import List, Optional, Tuple

from xml.etree import ElementTree as ET

ScxmlData = Tuple[str, Optional[str]]


class ScxmlDataModel:
    """This class represents the variables defined in the model."""
    def __init__(self, data_entries: List[ScxmlData] = None):
        self._data_entries = data_entries

    def check_validity(self) -> bool:
        valid_data_entries = True
        if self._data_entries is not None:
            valid_data_entries = isinstance(self._data_entries, list)
            if valid_data_entries:
                for data_entry in self._data_entries:
                    valid_data_entry = isinstance(data_entry, tuple) and len(data_entry) == 2
                    if not valid_data_entry:
                        valid_data_entries = False
                        break
                    name, expr = data_entry
                    valid_name = isinstance(name, str) and len(name) > 0
                    valid_expr = expr is None or isinstance(expr, str)
                    if not valid_name or not valid_expr:
                        valid_data_entries = False
                        break
        if not valid_data_entries:
            print("Error: SCXML datamodel: data entries are not valid.")
        return valid_data_entries

    def as_xml(self) -> Optional[ET.Element]:
        assert self.check_validity(), "SCXML: found invalid datamodel object."
        if self._data_entries is None or len(self._data_entries) == 0:
            return None
        xml_datamodel = ET.Element("datamodel")
        for data_entry in self._data_entries:
            name, expr = data_entry
            xml_data = ET.Element("data", {"id": name})
            if expr is not None:
                xml_data.set("expr", expr)
            xml_datamodel.append(xml_data)
        return xml_datamodel