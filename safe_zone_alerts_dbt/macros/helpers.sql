{% macro st_distance_meters(lon1, lat1, lon2, lat2) -%}
  ST_DISTANCE(ST_GEOGPOINT({{ lon1 }}, {{ lat1 }}), ST_GEOGPOINT({{ lon2 }}, {{ lat2 }}))
{%- endmacro %}
