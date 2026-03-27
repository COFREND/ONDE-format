### Geometric setup

**Description**

The geometric setup contains references to the inspected component, the probes and the trajectory. If the specimen
description is missing, a semi-infinite half-plane is assumed, with interface at z=0 and material for z>0.

**Trajectories**

ACQUISITION_TRAJECTORY gives references to the groups describing the trajectory -- references have the same order as
PROBE_LIST. PROBE_COORDINATE_FRAME can be used to define an offset between a referenced trajectory and the probe -
identity is assumed if not provided.