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
Declaration of SCXML tags related to ROS Services.

Additional information:
https://docs.ros.org/en/iron/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Services/Understanding-ROS2-Services.html
"""

from typing import Optional, List, Union
from scxml_converter.scxml_entries import (ScxmlBase, RosField, ScxmlSend, ScxmlTransition,
                                           ScxmlExecutionBody)
from scxml_converter.scxml_entries import (execution_body_from_xml, valid_execution_body,
                                           as_plain_execution_body)
from xml.etree import ElementTree as ET
from scxml_converter.scxml_entries.utils import ScxmlRosDeclarationsContainer
from scxml_converter.scxml_entries.utils import (is_srv_type_known, get_srv_type_params,
                                                 generate_srv_request_event,
                                                 generate_srv_response_event,
                                                 generate_srv_server_request_event,
                                                 generate_srv_server_response_event)


class RosServiceServer(ScxmlBase):
    """Object used in SCXML root to declare a new service server."""

    @staticmethod
    def get_tag_name() -> str:
        return "ros_service_server"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "RosServiceServer":
        """Create a RosServiceServer object from an XML tree."""
        assert xml_tree.tag == RosServiceServer.get_tag_name(), \
            f"Error: SCXML Service Server: XML tag name is not '{RosServiceServer.get_tag_name()}'."
        service_name = xml_tree.attrib.get("service_name")
        service_type = xml_tree.attrib.get("type")
        assert service_name is not None and service_type is not None, \
            "Error: SCXML Service Server: 'service_name' or 'type' cannot be found in input xml."
        return RosServiceServer(service_name, service_type)

    def __init__(self, srv_name: str, srv_type: str) -> None:
        """
        Initialize a new RosServiceServer object.

        :param srv_name: Topic used by the service.
        :param srv_type: ROS type of the service.
        """
        self._srv_name = srv_name
        self._srv_type = srv_type

    def get_service_name(self) -> str:
        """Get the name of the service."""
        return self._srv_name

    def get_service_type(self) -> str:
        """Get the type of the service."""
        return self._srv_type

    def check_validity(self) -> bool:
        valid_name = isinstance(self._srv_name, str) and len(self._srv_name) > 0
        valid_type = is_srv_type_known(self._srv_type)
        if not valid_name:
            print("Error: SCXML Service Server: service name is not valid.")
        if not valid_type:
            print("Error: SCXML Service Server: service type is not valid.")
        return valid_name and valid_type

    def as_plain_scxml(self, _) -> ScxmlBase:
        # This is discarded in the to_plain_scxml_and_declarations method from ScxmlRoot
        raise RuntimeError("Error: SCXML ROS declarations cannot be converted to plain SCXML.")

    def as_xml(self) -> ET.Element:
        assert self.check_validity(), "Error: SCXML Service Server: invalid parameters."
        xml_srv_server = ET.Element(
            RosServiceServer.get_tag_name(),
            {"service_name": self._srv_name, "type": self._srv_type})
        return xml_srv_server


class RosServiceClient(ScxmlBase):
    """Object used in SCXML root to declare a new service client."""

    @staticmethod
    def get_tag_name() -> str:
        return "ros_service_client"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "RosServiceClient":
        """Create a RosServiceClient object from an XML tree."""
        assert xml_tree.tag == RosServiceClient.get_tag_name(), \
            f"Error: SCXML Service Client: XML tag name is not '{RosServiceClient.get_tag_name()}'."
        service_name = xml_tree.attrib.get("service_name")
        service_type = xml_tree.attrib.get("type")
        assert service_name is not None and service_type is not None, \
            "Error: SCXML Service Client: 'service_name' or 'type' cannot be found in input xml."
        return RosServiceClient(service_name, service_type)

    def __init__(self, srv_name: str, srv_type: str) -> None:
        """
        Initialize a new RosServiceClient object.

        :param srv_name: Topic used by the service.
        :param srv_type: ROS type of the service.
        """
        self._srv_name = srv_name
        self._srv_type = srv_type

    def get_service_name(self) -> str:
        """Get the name of the service."""
        return self._srv_name

    def get_service_type(self) -> str:
        """Get the type of the service."""
        return self._srv_type

    def check_validity(self) -> bool:
        valid_name = isinstance(self._srv_name, str) and len(self._srv_name) > 0
        valid_type = is_srv_type_known(self._srv_type)
        if not valid_name:
            print("Error: SCXML Service Client: service name is not valid.")
        if not valid_type:
            print("Error: SCXML Service Client: service type is not valid.")
        return valid_name and valid_type

    def as_plain_scxml(self, _) -> ScxmlBase:
        # This is discarded in the to_plain_scxml_and_declarations method from ScxmlRoot
        raise RuntimeError("Error: SCXML ROS declarations cannot be converted to plain SCXML.")

    def as_xml(self) -> ET.Element:
        assert self.check_validity(), "Error: SCXML Service Client: invalid parameters."
        xml_srv_server = ET.Element(
            RosServiceClient.get_tag_name(),
            {"service_name": self._srv_name, "type": self._srv_type})
        return xml_srv_server


class RosServiceSendRequest(ScxmlSend):
    """Object representing a ROS service request (from the client side) in SCXML."""

    @staticmethod
    def get_tag_name() -> str:
        return "ros_service_send_request"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "RosServiceSendRequest":
        """Create a RosServiceServer object from an XML tree."""
        assert xml_tree.tag == RosServiceSendRequest.get_tag_name(), \
            "Error: SCXML service request: XML tag name is not " + \
            RosServiceSendRequest.get_tag_name()
        srv_name = xml_tree.attrib.get("service_name")
        assert srv_name is not None, \
            "Error: SCXML service request: 'service_name' attribute not found in input xml."
        fields = []
        for field_xml in xml_tree:
            fields.append(RosField.from_xml_tree(field_xml))
        if len(fields) == 0:
            fields = None
        return RosServiceSendRequest(srv_name, fields)

    def __init__(self,
                 service_decl: Union[str, RosServiceClient],
                 fields: Optional[List[RosField]]) -> None:
        """
        Initialize a new RosServiceSendRequest object.

        :param service_decl: Name of the service of Scxml obj. of Service Client declaration.
        :param fields: List of fields to be sent in the request.
        """
        if isinstance(service_decl, RosServiceClient):
            self._srv_name = service_decl.get_service_name()
        else:
            # Used for generating ROS entries from xml file
            assert isinstance(service_decl, str), \
                "Error: SCXML Service Send Request: invalid service name."
            self._srv_name = service_decl
        self._fields = fields
        assert self.check_validity(), "Error: SCXML Service Send Request: invalid parameters."

    def check_validity(self) -> bool:
        valid_name = isinstance(self._srv_name, str) and len(self._srv_name) > 0
        valid_fields = self._fields is None or \
            all([isinstance(field, RosField) and field.check_validity() for field in self._fields])
        if not valid_name:
            print("Error: SCXML service request: service name is not valid.")
        if not valid_fields:
            print("Error: SCXML service request: fields are not valid.")
        return valid_name and valid_fields

    def as_plain_scxml(self, ros_declarations: ScxmlRosDeclarationsContainer) -> ScxmlSend:
        service_type = ros_declarations.get_service_client_type(self._srv_name)
        # Get all params expected in the service request
        req_params, _ = get_srv_type_params(service_type)
        event_name = generate_srv_request_event(
            self._srv_name, ros_declarations.get_automaton_name())
        # Ensure all required fields are specified
        for field in self._fields:
            assert field.get_name() in req_params, \
                f"Error: SCXML service request: field {field.get_name()} not in {service_type}."
            req_params.pop(field.get_name())
        assert len(req_params) == 0, \
            f"Error: SCXML service request: missing fields {req_params}."
        event_params = [field.as_plain_scxml() for field in self._fields]
        return ScxmlSend(event_name, event_params)

    def as_xml(self) -> ET.Element:
        assert self.check_validity(), "Error: SCXML Service Send Request: invalid parameters."
        xml_srv_request = ET.Element(RosServiceSendRequest.get_tag_name(),
                                     {"service_name": self._srv_name})
        if self._fields is not None:
            for field in self._fields:
                xml_srv_request.append(field.as_xml())
        return xml_srv_request


class RosServiceHandleRequest(ScxmlTransition):
    """SCXML object representing a ROS service callback on the server, acting upon a request."""

    @staticmethod
    def get_tag_name() -> str:
        return "ros_service_handle_request"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "RosServiceHandleRequest":
        """Create a RosServiceServer object from an XML tree."""
        assert xml_tree.tag == RosServiceHandleRequest.get_tag_name(), \
            "Error: SCXML service request handler: XML tag name is not " +\
            RosServiceHandleRequest.get_tag_name()
        srv_name = xml_tree.attrib.get("service_name")
        target_name = xml_tree.attrib.get("target")
        assert srv_name is not None and target_name is not None, \
            "Error: SCXML service request handler: 'service_name' or 'target' attribute not " \
            "found in input xml."
        exec_body = execution_body_from_xml(xml_tree)
        return RosServiceHandleRequest(srv_name, target_name, exec_body)

    def __init__(self, service_decl: Union[str, RosServiceServer], target: str,
                 body: Optional[ScxmlExecutionBody] = None) -> None:
        """
        Initialize a new RosServiceHandleRequest object.

        :param service_decl: The service server declaration, or its name.
        :param target: Target state after the request has been received.
        :param body: Execution body to be executed upon request, before transitioning to target.
        """
        if isinstance(service_decl, RosServiceServer):
            self._service_name = service_decl.get_service_name()
        else:
            # Used for generating ROS entries from xml file
            assert isinstance(service_decl, str), \
                "Error: SCXML Service Handle Request: invalid service name."
            self._service_name = service_decl
        self._target = target
        self._body = body
        assert self.check_validity(), "Error: SCXML Service Handle Request: invalid parameters."

    def check_validity(self) -> bool:
        valid_name = isinstance(self._service_name, str) and len(self._service_name) > 0
        valid_target = isinstance(self._target, str) and len(self._target) > 0
        valid_body = self._body is None or valid_execution_body(self._body)
        if not valid_name:
            print("Error: SCXML Service Handle Request: service name is not valid.")
        if not valid_target:
            print("Error: SCXML Service Handle Request: target is not valid.")
        if not valid_body:
            print("Error: SCXML Service Handle Request: body is not valid.")
        return valid_name and valid_target and valid_body

    def as_plain_scxml(self, ros_declarations: ScxmlRosDeclarationsContainer) -> ScxmlTransition:
        event_name = generate_srv_server_request_event(self._service_name)
        target = self._target
        body = as_plain_execution_body(self._body, ros_declarations)
        return ScxmlTransition(target, [event_name], None, body)

    def as_xml(self) -> ET.Element:
        assert self.check_validity(), "Error: SCXML Service Handle Request: invalid parameters."
        xml_srv_request = ET.Element(RosServiceHandleRequest.get_tag_name(),
                                     {"service_name": self._service_name, "target": self._target})
        if self._body is not None:
            for body_elem in self._body.as_xml():
                xml_srv_request.append(body_elem)
        return xml_srv_request


class RosServiceSendResponse(ScxmlSend):
    """SCXML object representing the response from a service server."""

    @staticmethod
    def get_tag_name() -> str:
        return "ros_service_send_response"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "RosServiceClient":
        """Create a RosServiceServer object from an XML tree."""
        assert xml_tree.tag == RosServiceSendResponse.get_tag_name(), \
            "Error: SCXML service response: XML tag name is not " + \
            RosServiceSendResponse.get_tag_name()
        srv_name = xml_tree.attrib.get("service_name")
        assert srv_name is not None, \
            "Error: SCXML service response: 'service_name' attribute not found in input xml."
        fields = []
        for field_xml in xml_tree:
            fields.append(RosField.from_xml_tree(field_xml))
        if len(fields) == 0:
            fields = None
        return RosServiceSendResponse(srv_name, fields)

    def __init__(self, service_name: Union[str, RosServiceServer],
                 fields: Optional[List[RosField]]) -> None:
        """
        Initialize a new RosServiceClient object.

        :param service_name: Topic used by the service.
        :param fields: List of fields to be sent in the response.
        """
        if isinstance(service_name, RosServiceServer):
            self._service_name = service_name.get_service_name()
        else:
            # Used for generating ROS entries from xml file
            assert isinstance(service_name, str), \
                "Error: SCXML Service Send Response: invalid service name."
            self._service_name = service_name
        self._fields = fields
        assert self.check_validity(), "Error: SCXML Service Send Response: invalid parameters."

    def check_validity(self) -> bool:
        valid_name = isinstance(self._service_name, str) and len(self._service_name) > 0
        valid_fields = self._fields is None or \
            all([isinstance(field, RosField) and field.check_validity() for field in self._fields])
        if not valid_name:
            print("Error: SCXML service response: service name is not valid.")
        if not valid_fields:
            print("Error: SCXML service response: fields are not valid.")
        return valid_name and valid_fields

    def as_plain_scxml(self, ros_declarations: ScxmlRosDeclarationsContainer) -> ScxmlSend:
        service_type = ros_declarations.get_service_server_type(self._service_name)
        # Get all params expected in the service response
        _, res_params = get_srv_type_params(service_type)
        event_name = generate_srv_server_response_event(self._service_name)
        # Ensure all required fields are specified
        for field in self._fields:
            assert field.get_name() in res_params, \
                f"Error: SCXML service response: field {field.get_name()} not in {service_type}."
            res_params.pop(field.get_name())
        assert len(res_params) == 0, \
            f"Error: SCXML service server response: missing fields {res_params}."
        event_params = [field.as_plain_scxml() for field in self._fields]
        return ScxmlSend(event_name, event_params)

    def as_xml(self) -> ET.Element:
        assert self.check_validity(), "Error: SCXML Service Send Response: invalid parameters."
        xml_srv_response = ET.Element(RosServiceSendResponse.get_tag_name(),
                                      {"service_name": self._service_name})
        if self._fields is not None:
            for field in self._fields:
                xml_srv_response.append(field.as_xml())
        return xml_srv_response


class RosServiceHandleResponse(ScxmlTransition):
    """SCXML object representing the handler of a service response for a service client."""

    @staticmethod
    def get_tag_name() -> str:
        return "ros_service_handle_response"

    @staticmethod
    def from_xml_tree(xml_tree: ET.Element) -> "RosServiceClient":
        """Create a RosServiceServer object from an XML tree."""
        pass

    def __init__(self, service_decl: Union[str, RosServiceClient], target: str,
                 body: Optional[ScxmlExecutionBody] = None) -> None:
        """
        Initialize a new RosServiceClient object.

        :param service_name: Topic used by the service.
        :param type: ROS type of the service.
        """
        pass

    def check_validity(self) -> bool:
        pass

    def as_plain_scxml(self, _) -> ScxmlTransition:
        pass

    def as_xml(self) -> ET.Element:
        pass
