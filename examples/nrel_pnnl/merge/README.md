# Merged Files

`merge.py` invokes the prototype "merge" method developed in the `brickschema` package. It requires both graphs to have the same namespace for their entities, and it requires each entity to have an `rdfs:label`. The input graphs are both validated and the output graph is also validated. Brick `nightly` is used to perform reasoning on the graphs as part of the merge process but the merged graph will not contain Brick.
