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

"""Declaration of ROS-Specific SCXML tags extensions."""

from typing import Union
from scxml_converter.scxml_entries import (
    RosTimeRate, RosTopicPublisher, RosTopicSubscriber, RosServiceServer, RosServiceClient,
    RosServiceHandleRequest, RosServiceHandleResponse,
    RosServiceSendRequest, RosServiceSendResponse,
    RosTopicPublish, RosTopicCallback, RosRateCallback)

ScxmlRosDeclarations = Union[RosTimeRate, RosTopicPublisher, RosTopicSubscriber,
                             RosServiceServer, RosServiceClient]

# List of Ros entries inheriting from ScxmlTransition
ScxmlRosTransitions = (RosServiceHandleRequest, RosServiceHandleResponse,
                       RosTopicCallback, RosRateCallback)

# List of Ros entries inheriting from ScxmlSend
ScxmlRosSends = (RosServiceSendRequest, RosServiceSendResponse, RosTopicPublish)
