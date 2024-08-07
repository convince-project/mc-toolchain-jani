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
Representation of ROS Services.
"""

from typing import Dict, List, Optional

from jani_generator.jani_entries import JaniModel
from scxml_converter.scxml_entries import (ScxmlAssign, ScxmlData,
                                           ScxmlDataModel, ScxmlParam,
                                           ScxmlRoot, ScxmlSend, ScxmlState,
                                           ScxmlTransition)
from scxml_converter.scxml_entries.utils import (
    generate_srv_request_event, generate_srv_response_event,
    generate_srv_server_request_event, generate_srv_server_response_event,
    get_default_expression_for_type, get_srv_type_params,
    sanitize_ros_interface_name)

SRV_PREFIX = "srv_handler_"


class RosService:
    """Object that contains a description of a ROS service with its server and clients."""

    def __init__(self):
        self._service_name: Optional[str] = None
        self._service_type: Optional[str] = None
        self._service_server_automaton: Optional[str] = None
        self._service_client_automata: List[str] = []

    def _set_name_and_type(self, service_name: str, service_type: str) -> None:
        if self._service_name is None:
            self._service_name = service_name
            self._service_type = service_type
        else:
            assert self._service_name == service_name, \
                f"Service name {service_name} does not match {self._service_name}."
            assert self._service_type == service_type, \
                f"Service type {service_type} does not match {self._service_type}."

    def _assert_validity(self):
        """
        Make sure service_name and service_type are set and a server and at least one client exist.
        """
        assert self._service_name is not None, "Service name not set."
        assert self._service_type is not None, "Service type not set."
        assert self._service_server_automaton is not None, \
            f"Service server not set for {self._service_name}."
        assert len(self._service_client_automata) > 0, \
            f"No service clients set for {self._service_name}."

    def set_service_server(self, service_name: str, service_type: str, automaton_name: str) -> None:
        """
        Set the server of the service.
        There must be exactly one.

        :service_name: The name of the ROS service.
        :service_type: The type of the ROS service (e.g. std_srvs/SetBool).
        :automaton_name: The name of the JANI automaton that implements this server.
        """
        self._set_name_and_type(service_name, service_type)
        assert self._service_server_automaton is None, \
            f"Found more than one server for service {service_name}."
        self._service_server_automaton = automaton_name

    def append_service_client(self,
                              service_name: str, service_type: str, automaton_name: str) -> None:
        """
        Set the client of the service.
        There must be one or more.

        :service_name: The name of the ROS service.
        :service_type: The type of the ROS service (e.g. std_srvs/SetBool).
        :automaton_name: The name of the JANI automaton that implements this client.
        """
        self._set_name_and_type(service_name, service_type)
        assert automaton_name not in self._service_client_automata, \
            f"Service client for {automaton_name} already declared for service {service_name}."
        self._service_client_automata.append(automaton_name)

    def to_scxml(self) -> ScxmlRoot:
        """
        Generate the srv_handler automaton that implements the link between the server of this
        service and its clients.
        This ensures that only one request can be processed at the time and that the client receives
        only the response related to it's request.

        :return: Scxml object representing the necessary file content.
        """
        self._assert_validity()
        req_params, res_params = get_srv_type_params(self._service_type)
        # Hack: Using support variables in the data model to avoid having _event in send params
        req_fields_as_data = []
        for field_name, field_type in req_params.items() | res_params.items():
            default_expr = get_default_expression_for_type(field_type)
            req_fields_as_data.append(ScxmlData(field_name, default_expr, field_type))
        # Make sure the service name has no slashes and spaces
        scxml_root_name = SRV_PREFIX + sanitize_ros_interface_name(self._service_name)
        wait_state = ScxmlState("waiting",
                                body=[
                                    ScxmlTransition(
                                        f"processing_client_{client_id}",
                                        [generate_srv_request_event(self._service_name, client_id)],
                                        body=[ScxmlAssign(field_name, f"_event.{field_name}") for
                                              field_name in req_params] + [
                                            ScxmlSend(generate_srv_server_request_event(
                                                      self._service_name),
                                                      [ScxmlParam(field_name, expr=field_name) for
                                                       field_name in req_params])])
                                    for client_id in self._service_client_automata])
        processing_states = [
            ScxmlState(f"processing_client_{client_id}",
                       body=[
                           ScxmlTransition(
                               "waiting", [generate_srv_server_response_event(self._service_name)],
                               body=[
                                   ScxmlAssign(field_name, f"_event.{field_name}") for
                                   field_name in res_params] + [
                                       ScxmlSend(generate_srv_response_event(
                                           self._service_name, client_id),
                                           [ScxmlParam(field_name, expr=field_name) for
                                            field_name in res_params])])])
            for client_id in self._service_client_automata]
        # Prepare the ScxmlRoot object and return it
        scxml_root = ScxmlRoot(scxml_root_name)
        scxml_root.set_data_model(ScxmlDataModel(req_fields_as_data))
        scxml_root.add_state(wait_state, initial=True)
        for processing_state in processing_states:
            scxml_root.add_state(processing_state)
        assert scxml_root.is_plain_scxml(), "Generated SCXML for srv sync is not plain SCXML."
        return scxml_root


# Mapping from RosService name and RosService information
RosServices = Dict[str, RosService]


def remove_empty_self_loops_from_srv_handlers_in_jani(jani_model: JaniModel) -> None:
    """
    Remove self-loops from srv_handler automata in the Jani model.

    :param jani_model: The Jani model to modify.
    """
    for automaton in jani_model.get_automata():
        # Modify the automaton in place
        if automaton.get_name().startswith(SRV_PREFIX):
            automaton.remove_empty_self_loop_edges()
