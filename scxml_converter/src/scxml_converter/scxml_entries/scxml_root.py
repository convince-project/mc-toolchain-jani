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
The main entry point of an SCXML Model. In XML, it has the tag `scxml`.
"""

from copy import deepcopy
from os.path import isfile
from typing import List, Optional, Tuple, get_args
from xml.etree import ElementTree as ET

from scxml_converter.scxml_entries import (RosServiceClient, RosServiceServer,
                                           RosTimeRate, RosTopicPublisher,
                                           RosTopicSubscriber, ScxmlBase,
                                           ScxmlDataModel,
                                           ScxmlRosDeclarations,
                                           ScxmlRosDeclarationsContainer,
                                           ScxmlState)


class ScxmlRoot(ScxmlBase):
    """This class represents a whole scxml model, that is used to define specific skills."""

    @staticmethod
    def get_tag_name() -> str:
        return "scxml"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "ScxmlRoot":
        """Create a ScxmlRoot object from an XML tree."""
        # --- Get the ElementTree objects
        assert xml_tree.tag == ScxmlRoot.get_tag_name(), \
            f"Error: SCXML root: XML root tag {xml_tree.tag} is not {ScxmlRoot.get_tag_name()}."
        assert "name" in xml_tree.attrib, \
            "Error: SCXML root: 'name' attribute not found in input xml."
        assert "version" in xml_tree.attrib and xml_tree.attrib["version"] == "1.0", \
            "Error: SCXML root: 'version' attribute not found or invalid in input xml."
        # Data Model
        datamodel_elements = xml_tree.findall(ScxmlDataModel.get_tag_name())
        assert datamodel_elements is None or len(datamodel_elements) <= 1, \
            f"Error: SCXML root: {len(datamodel_elements)} datamodels found, max 1 allowed."
        # ROS Declarations
        ros_declarations: List[ScxmlRosDeclarations] = []
        for child in xml_tree:
            if child.tag == RosTimeRate.get_tag_name():
                ros_declarations.append(RosTimeRate.from_xml_tree(child))
            elif child.tag == RosTopicSubscriber.get_tag_name():
                ros_declarations.append(RosTopicSubscriber.from_xml_tree(child))
            elif child.tag == RosTopicPublisher.get_tag_name():
                ros_declarations.append(RosTopicPublisher.from_xml_tree(child))
            elif child.tag == RosServiceServer.get_tag_name():
                ros_declarations.append(RosServiceServer.from_xml_tree(child))
            elif child.tag == RosServiceClient.get_tag_name():
                ros_declarations.append(RosServiceClient.from_xml_tree(child))
        # States
        assert "initial" in xml_tree.attrib, \
            "Error: SCXML root: 'initial' attribute not found in input xml."
        initial_state = xml_tree.attrib["initial"]
        state_elements = xml_tree.findall(ScxmlState.get_tag_name())
        assert state_elements is not None and len(state_elements) > 0, \
            "Error: SCXML root: no state found in input xml."
        # Fill Data in the ScxmlRoot object
        scxml_root = ScxmlRoot(xml_tree.attrib["name"])
        # Data Model
        if datamodel_elements is not None and len(datamodel_elements) > 0:
            scxml_root.set_data_model(ScxmlDataModel.from_xml_tree(datamodel_elements[0]))
        # ROS Declarations
        scxml_root._ros_declarations = ros_declarations
        # States
        for state_element in state_elements:
            scxml_state = ScxmlState.from_xml_tree(state_element)
            is_initial = scxml_state.get_id() == initial_state
            scxml_root.add_state(scxml_state, initial=is_initial)
        return scxml_root

    @staticmethod
    def from_scxml_file(xml_file: str) -> "ScxmlRoot":
        """Create a ScxmlRoot object from an SCXML file."""
        if isfile(xml_file):
            xml_element = ET.parse(xml_file).getroot()
        elif xml_file.startswith("<?xml"):
            xml_element = ET.fromstring(xml_file)
        else:
            raise ValueError(f"Error: SCXML root: xml_file '{xml_file}' isn't a file / xml string.")
        # Remove the namespace from all tags in the XML file
        for child in xml_element.iter():
            if "{" in child.tag:
                child.tag = child.tag.split("}")[1]
        # Do the conversion
        return ScxmlRoot.from_xml_tree(xml_element)

    def __init__(self, name: str):
        self._name = name
        self._version = "1.0"  # This is the only version mentioned in the official documentation
        self._initial_state: Optional[str] = None
        self._states: List[ScxmlState] = []
        self._data_model: Optional[ScxmlDataModel] = None
        self._ros_declarations: List[ScxmlRosDeclarations] = []

    def get_name(self) -> str:
        """Get the name of the automaton represented by this SCXML model."""
        return self._name

    def get_initial_state_id(self) -> str:
        """Get the ID of the initial state of the SCXML model."""
        assert self._initial_state is not None, "Error: SCXML root: Initial state not set."
        return self._initial_state

    def get_data_model(self) -> Optional[ScxmlDataModel]:
        return self._data_model

    def get_states(self) -> List[ScxmlState]:
        return self._states

    def get_state_by_id(self, state_id: str) -> Optional[ScxmlState]:
        for state in self._states:
            if state.get_id() == state_id:
                return state
        return None

    def add_state(self, state: ScxmlState, *, initial: bool = False):
        """Append a state to the list of states. If initial is True, set it as the initial state."""
        self._states.append(state)
        if initial:
            assert self._initial_state is None, "Error: SCXML root: Initial state already set"
            self._initial_state = state.get_id()

    def set_data_model(self, data_model: ScxmlDataModel):
        assert self._data_model is None, "Data model already set"
        self._data_model = data_model

    def add_ros_declaration(self, ros_declaration: ScxmlRosDeclarations):
        assert isinstance(ros_declaration, get_args(ScxmlRosDeclarations)), \
            "Error: SCXML root: invalid ROS declaration type."
        assert ros_declaration.check_validity(), "Error: SCXML root: invalid ROS declaration."
        if self._ros_declarations is None:
            self._ros_declarations = []
        self._ros_declarations.append(ros_declaration)

    def _generate_ros_declarations_helper(self) -> Optional[ScxmlRosDeclarationsContainer]:
        """Generate a HelperRosDeclarations object from the existing ROS declarations."""
        ros_decl_container = ScxmlRosDeclarationsContainer(self._name)
        if self._ros_declarations is not None:
            for ros_declaration in self._ros_declarations:
                if not ros_declaration.check_validity():
                    return None
                if isinstance(ros_declaration, RosTimeRate):
                    ros_decl_container.append_timer(ros_declaration.get_name(),
                                                    ros_declaration.get_rate())
                elif isinstance(ros_declaration, RosTopicSubscriber):
                    ros_decl_container.append_subscriber(ros_declaration.get_topic_name(),
                                                         ros_declaration.get_topic_type())
                elif isinstance(ros_declaration, RosTopicPublisher):
                    ros_decl_container.append_publisher(ros_declaration.get_topic_name(),
                                                        ros_declaration.get_topic_type())
                elif isinstance(ros_declaration, RosServiceServer):
                    ros_decl_container.append_service_server(ros_declaration.get_service_name(),
                                                             ros_declaration.get_service_type())
                elif isinstance(ros_declaration, RosServiceClient):
                    ros_decl_container.append_service_client(ros_declaration.get_service_name(),
                                                             ros_declaration.get_service_type())
                else:
                    raise ValueError("Error: SCXML root: invalid ROS declaration type.")
        return ros_decl_container

    def check_validity(self) -> bool:
        valid_name = isinstance(self._name, str) and len(self._name) > 0
        valid_initial_state = self._initial_state is not None
        valid_states = isinstance(self._states, list) and len(self._states) > 0
        if valid_states:
            for state in self._states:
                valid_states = isinstance(state, ScxmlState) and state.check_validity()
                if not valid_states:
                    break
        valid_data_model = self._data_model is None or self._data_model.check_validity()
        if not valid_name:
            print("Error: SCXML root: name is not valid.")
        if not valid_initial_state:
            print("Error: SCXML root: no initial state set.")
        if not valid_states:
            print("Error: SCXML root: states are not valid.")
        if not valid_data_model:
            print("Error: SCXML root: datamodel is not valid.")
        valid_ros = self._check_valid_ros_declarations()
        if not valid_ros:
            print("Error: SCXML root: ROS declarations are not valid.")
        return valid_name and valid_initial_state and valid_states and valid_data_model and \
            valid_ros

    def _check_valid_ros_declarations(self) -> bool:
        """Check if the ros declarations and instantiations are valid."""
        # Prepare the ROS declarations, to check no undefined ros instances exist
        ros_decl_container = self._generate_ros_declarations_helper()
        if ros_decl_container is None:
            return False
        # Check the ROS instantiations
        for state in self._states:
            if not state.check_valid_ros_instantiations(ros_decl_container):
                return False
        return True

    def is_plain_scxml(self) -> bool:
        """Check whether there are ROS specific features or all entries are plain SCXML."""
        assert self.check_validity(), "SCXML: found invalid root object."
        # If this is a valid scxml object, checking the absence of declarations is enough
        return self._ros_declarations is None or len(self._ros_declarations) == 0

    def to_plain_scxml_and_declarations(self) -> Tuple["ScxmlRoot", ScxmlRosDeclarationsContainer]:
        """
        Convert all internal ROS specific entries to plain SCXML.

        :return: A tuple with:
            - a new ScxmlRoot object with all ROS specific entries converted to plain SCXML
            - A list of timers with related rate in Hz
        """
        if self.is_plain_scxml():
            return self, ScxmlRosDeclarationsContainer(self._name)
        # Convert the ROS specific entries to plain SCXML
        plain_root = ScxmlRoot(self._name)
        plain_root._data_model = deepcopy(self._data_model)
        plain_root._initial_state = self._initial_state
        ros_declarations = self._generate_ros_declarations_helper()
        assert ros_declarations is not None, "Error: SCXML root: invalid ROS declarations."
        plain_root._states = [state.as_plain_scxml(ros_declarations) for state in self._states]
        assert plain_root.is_plain_scxml(), "SCXML root: conversion to plain SCXML failed."
        return (plain_root, ros_declarations)

    def as_xml(self) -> ET.Element:
        assert self.check_validity(), "SCXML: found invalid root object."
        assert self._initial_state is not None, "Error: SCXML root: no initial state set."
        xml_root = ET.Element("scxml", {
            "name": self._name,
            "version": self._version,
            "model_src": "",
            "initial": self._initial_state,
            "xmlns": "http://www.w3.org/2005/07/scxml"
        })
        if self._data_model is not None:
            data_model_xml = self._data_model.as_xml()
            assert data_model_xml is not None, "Error: SCXML root: invalid data model."
            xml_root.append(data_model_xml)
        if self._ros_declarations is not None:
            for ros_declaration in self._ros_declarations:
                xml_root.append(ros_declaration.as_xml())
        for state in self._states:
            xml_root.append(state.as_xml())
        ET.indent(xml_root, "    ")
        return xml_root

    def as_xml_string(self) -> str:
        return ET.tostring(self.as_xml(), encoding='unicode', xml_declaration=True)
