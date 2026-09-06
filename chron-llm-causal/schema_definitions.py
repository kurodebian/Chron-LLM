"""
FRR-v1.2 Normative JSON Schema Definitions
JSON Schema Draft 2020-12 / Strict
"""

FRR_RULE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "frr-rule-v1.2.schema.json",
    "title": "FRR Rule",
    "type": "object",

    "required": [
        "rule_id",
        "rule_type",
        "source_type",
        "component_id",
        "record_scope",
        "normalized_pattern",
        "target_id",
        "evidence_ref",
    ],

    "properties": {
        "rule_id": {
            "type": "string",
            "minLength": 1,
        },

        # Rule table / semantic domain
        "rule_type": {
            "type": "string",
            "enum": [
                "ALIAS",
                "TRANSFORM",
                "RELATION_NORMALIZATION",
                "SPEC_BINDING",
                "AUTHORITY",
            ],
        },

        # Target entity type
        "source_type": {
            "type": "string",
            "enum": [
                "NODE",
                "EDGE",
                "SPEC",
                "AUTHORITY",
            ],
        },

        "component_id": {
            "type": "string",
            "minLength": 1,
        },

        "record_scope": {
            "type": "object",
            "required": [
                "domain",
                "entity_type",
            ],
            "properties": {
                "domain": {
                    "type": "string",
                },
                "entity_type": {
                    "type": "string",
                },
            },
            "additionalProperties": False,
        },

        "normalized_pattern": {
            "type": "object",
            "required": [
                "type",
                "value",
            ],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "EXACT",
                        "PREFIX",
                        "PREFIX_CHARSET",
                        "SUFFIX",
                    ],
                },

                "value": {
                    "type": "string",
                },

                "charset": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1,
                    },
                    "uniqueItems": True,
                },
            },
            "additionalProperties": False,
        },

        "target_id": {
            "type": "string",
            "minLength": 1,
        },

        "evidence_ref": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
            },
            "uniqueItems": True,
        },
    },

    "additionalProperties": False,
}


FRR_PACKAGE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "frr-package-v1.2.schema.json",
    "title": "FRR Integrity Package",
    "type": "object",

    "required": [
        "ruleset_hash",
        "integrity",
        "rules",
    ],

    "properties": {
        "ruleset_hash": {
            "type": "string",
            "pattern": "^[a-fA-F0-9]{64}$",
        },

        "integrity": {
            "type": "object",
            "required": [
                "algorithm",
                "signature",
            ],
            "properties": {
                "algorithm": {
                    "type": "string",
                    "enum": [
                        "Ed25519",
                    ],
                },

                "signature": {
                    "type": "string",
                    "pattern": "^[a-fA-F0-9]{128}$",
                },
            },
            "additionalProperties": False,
        },

        "rules": {
            "type": "array",
            "items": FRR_RULE_SCHEMA,
        },
    },

    "additionalProperties": False,
}