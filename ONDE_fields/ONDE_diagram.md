```mermaid
classDiagram
  ascan_dataset "0..1" o-- setup
  tscan_dataset "0..1" o-- setup
  cscan_dataset "0..1" o-- setup
  setup "1" o-- geometric_setup
  setup "0..1" o-- ultrasonic_setup
  ultrasonic_setup "0..n" o-- transmit_law
  ultrasonic_setup "0..n" o-- receive_law
  ultrasonic_setup "0..1" o-- phased_array_setup
  geometric_setup "1..n" o-- probe
  geometric_setup "1..n" o-- acquisition_trajectory
  geometric_setup  "0..1" o-- component
```
