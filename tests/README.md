# Tests

## Validation Tests
We demonstrate the usage of SHACL shapes against Haystack RDF documents. The validation tests are in `test_validation.py`. The original testing has been defined to help answer the common questions:
- Does Equipment X have the expected set of points I desire?

We define instance data (data graphs) and expected shapes (shape graphs) for two 'point sets' and an example AHU type that requires the two point types exactly once. The data graph is available in the `occupancy_mode_data.ttl` and the shape graph is available in the `occupancy_mode_shapes.ttl` file. The point types look as follows:
- OccupancyModeBinary:
    - Markers: {point, occupied, sp}
- OccupancyModeStandby:
    - Markers: {point, occ, mode, sp}
    - Key / values: {enum: "Occupied,Unoccupied,Standby"}

The instance data consists of the following entities:
- AHU-01, with the following points:
    - AHU-01-Point-01: conforms to the OccupancyModeStandby point type
    - AHU-01-Point-02: conforms to the OccupancyModeBinary point type

We add targets to the shapes on a test-by-test basis to keep the shapes generic. We perform tests for the following:

### OccupancyModeStandby Shape
- `AHU-01-Point-01` validates against the OccupancyModeStandby shape
- `AHU-01-Point-01` does not validate against the OccupancyModeStandby shape when the following are removed:
    - Scenario 1: remove the `occ` tag (raises one error)
    - Scenario 2: remove the `mode` tag (raises one error)
    - Scenario 3: remove the `mode` and `sp` tags (raises two errors, one for each tag)

### OccupancyModeBinary Shape
- `AHU-01-Point-02` validates against the OccupancyModeBinary shape
- `AHU-01-Point-02` does not validate against the OccupancyModeBinary shape when the following are removed:
    - Scenario 1: remove the `occupied` tag (raises one error)
    - Scenario 2: remove the `sp` tag (raises one error)
    - Scenario 3: remove the `occupied` and `sp` tags (raises two errors, one for each tag removed)

### AhuOccupancyShape
- `AHU-01` validates against the `AhuOccupancyShape` (i.e. it has the required points and the points are correctly defined)
- `AHU-01` does not validate against the `AhuOccupancyShape` when:
    - Scenario 1: `point` tag removed from `AHU-01-Point-01` - violates the `sh:QualifiedMinCountConstraintComponent` with respect to the `OccupancyModeStandby` shape
    - Scenario 2: `point` tag removed from `AHU-01-Point-01` and `sp` tag removed from `AHU-01-Point-02` - results in two violations:
        - Missing a point conforming to OccupancyModeStandby (as expected)
        - Missing a point conforming to OccupancyModeBinary (as expected)
    - Scenario 3: additional point added that also conforms to the `OccupancyModeBinary` shape. Intent here is to ensure only one of each point type is defined. Results in a `sh:QualifiedMaxCountConstraintComponent` with respect to the `OccupancyModeBinary` shape. Interpret as: __"You have too many points defined conforming to the OccupancyModeBinary shape"__
    - Scenario 4: remove the `AHU-01-Point-02`, but add the `occupied` tag to the `AHU-01-Point-01`. This is to test the 'disjoint shapes' requirement, i.e. that we actually want there to be distinct points conforming to each shape, and not one point that conforms to multiple point shapes and fulfills the requirements. In experimenting with this test, the results returned were not as intuitive as expected. Basically what you get is two validation errors, where both the `OccupancyModeBinary` and `OccupancyModeStandby` shapes do not meet the minimum count requirements, which isn't super intuitive.  The other methodology is to just specify the minimum number of points expected, which is a roundabout way of ensuring that a single point doesn't conform to multiple point type definitions. This leads to a more intuitive error: __"Less than 2 values on sample:AHU-01->[ sh:inversePath phIoT:equipRef ]"__.  Both the disjoint requirements and the minimum number of points requirements are left in the shape for verbosity sake.
