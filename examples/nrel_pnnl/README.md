# NREL-PNNL Reference Implementations
## Directories

### `merge/` 
Contains the `merge.py` script to merge the NREL (mechanical) and PNNL (electrical) models and resulting merged model.

### `nrel/`
Contains the NREL model of the mechanical systems.

### `pnnl/`
Contains the PNNL model of the electrical systems (lighting).

## Queries
The following SPARQL queries were used for the publication.

### NREL Mechanical Model

```turtle
# zone uri (subject), area, volume, clg capacity, and htg capacity
SELECT DISTINCT ?sub ?area ?volume ?clg ?htg
WHERE {
    ?sub a brick:HVAC_Zone ;
    brick:area/brick:value ?area ;
    brick:volume/brick:value ?volume ;
    brick:coolingCapacity/brick:value ?clg ;
    brick:ratedPowerOutput/brick:value ?htg .
} 
```

### PNNL Electrical Model

```turtle
TODO
```

### NREL-PNNL Merged Model

#### Electrical

```turtle
TODO
```

#### Mechanical

```turtle
Same query as NREL Mechanical Model.
```

#### Electrical-Mechanical

```turtle
# zone lighting power
SELECT DISTINCT ?zone (SUM(?ltg_pwr) as ?ltg_pwr_tot)
WHERE {
  	?zone a brick:HVAC_Zone ;
  		  brick:hasPart ?room .
  	?sub ?pre ?obj .
  		  ?sub brick:hasLocation ?room .
		?sub brick:ratedPowerInput/brick:value ?ltg_pwr .
}
GROUP BY ?zone

# zone room area
SELECT DISTINCT ?zone (SUM(?room_area) as ?room_area_tot)
WHERE {
  	?zone a brick:HVAC_Zone ;
  		  brick:hasPart ?room .
  	?room brick:grossArea/brick:value ?room_area .
}
GROUP BY ?zone
```
