SCXML to Jani Conversion
========================

SCXML and Jani
----------------

In CONVINCE, we expect developers to use Behavior Trees and SCXML to model the different parts of a robotic systems.

SCXML (Scope XML) is an high level format that describes a single state machine, and allows it to exchange information with other state machines using events. Each SCXML file defines its variables (datamodel), states and transitions.

With SCXML, the system consists of a set of state machines, each one represented by a SCXML file, that are synchronized together using events. Operations are carried out when a state machine receives an event, enters a state, or exits a state.

With Jani, the whole system is contained in a single JSON file, consisting of a set of global variables, automata (equivalent to state machines) with their edges (equivalent to transitions), and a composition description, describing how Automata should be synchronized by the mean of advancing specific edges at the same time.

The main difference between SCXML and Jani is that in Jani there is no concept of events, so synchronization must be achieved using the global variables and composition description.

High-Level (ROS) SCXML Implementation
---------------------------------------

In CONVINCE, we extended the standard SCXML format defined `here <https://www.w3.org/TR/scxml/>`_ with ROS specific features, to make it easier for ROS developers to model ROS-based systems.

In this guide we will refer to the extended SCXML format as High-Level SCXML and the standard SCXML format as Low-Level SCXML.

Currently, the supported ROS-features are:
- ROS Topics
- ROS Timers (Rate-callbacks)

TODO: Example of Topic and Timer declaration + usage.

Low-Level SCXML Conversion
----------------------------

Low-Level SCXML is the standard SCXML format defined `here <https://www.w3.org/TR/scxml/>`_.

Our converter is able to convert High-Level SCXML to Low-Level SCXML by translating the ROS specific features to standard SCXML features.
In case of timers, we need additional information that cannot be encoded in SCXML, so that information is generated at runtime.

The conversion between the two SCXML formats is implemented in ScxmlRoot.as_plain_scxml(). TODO: Link to API.

TODO: Describe how we translate the High-Level SCXML to the Low-Level SCXML.

Jani Conversion
----------------

Once the Low-Level SCXML is obtained, we can use it together with the timers information in the conversion to a Jani model.

Simple Overview
________________

The following picture gives a simple overview of how our conversion works:

.. image:: graphics/scxml_to_jani.drawio.svg
    :alt: Conversion process
    :align: center

The core of the conversion lies in the translation of the SCXML state machines to Jani automata and the handling of the synchronization between them.
In the example above, we have two SCXML state machines, BatteryDrainer and BatteryManager, that are synchronized using the event "level".

At start, the BatteryDrainer state machine sends a "level" event out, containing the current battery level in the "data" field.
In Jani, this translates to an edge, i.e. "level_on_send", that advances the BatteryDrainer automaton to a next state where the sending action is carried out and, at the same time, assigns a global variable corresponding to the event parameter, i.e. "level.data", and another edge with the same name that advances an additional automaton "level_sync" from the "wait" to the "received" state, signaling that an event "level" was sent out and needs to be processed.

The BatteryManager automaton has an edge "level_on_receive", that can now be triggered since the "level_sync" automaton is in the "received" state. When executing the edge, the BatteryManager automaton assigns the global variable "battery_alarm" based on the data contained in the "level.data" variable and goes back to the same state, waiting for the next "level" event. Similarly, the "level_sync" automaton transitions back to the "wait" state using the edge "level_on_receive".

The BatteryDrainer can execute the edge "battery_drainer_act_0" and transition back to the initial state either before or after the "level_on_receive" action, as there is no constraint enforcing a specific order of execution.

Similarly, since the automaton "level_sync" has an outgoing edge "level_on_send" that stays in the "received" state, the BatteryManager can send a "level" event before the BatteryDrainer has processed the previous one.
This has been introduced to make the synchronization more similar to how it works in ROS, where messages can be overridden before being processed.

Handling onentry, onexit and conditions
________________________________________

TODO

.. image:: graphics/scxml_to_jani_entry_exit_if.drawio.svg
    :alt: How execution blocks and conditions are translated
    :align: center

Handling of (ROS) Timers
__________________________

TODO