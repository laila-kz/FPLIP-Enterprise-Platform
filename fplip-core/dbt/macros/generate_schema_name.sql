{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {%- if custom_schema_name == 'gold' -%}
            fplip_gold
        {%- elif custom_schema_name == 'silver' -%}
            fplip_silver
        {%- else -%}
            {{ custom_schema_name | trim }}
        {%- endif -%}
    {%- endif -%}
{%- endmacro %}