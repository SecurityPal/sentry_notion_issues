from typing import Any


def initialize_empty_properties(property_schema: dict[str, Any]) -> dict[str, Any]:
    """Initialize empty property values for all property types in the schema.

    Args:
        property_schema: The database property schema

    Returns:
        Dictionary of property ID to empty property value

    """
    properties_object: dict[str, Any] = {}

    for prop_name, prop in property_schema.items():
        prop_type = getattr(prop, "type", None)
        if not prop_type:
            continue

        if prop_type == "title":
            # Skip title as it's typically set explicitly
            pass
        elif prop_type == "rich_text":
            properties_object[prop_name] = {"rich_text": []}
        elif prop_type == "number":
            properties_object[prop_name] = {"number": None}
        elif prop_type == "select":
            properties_object[prop_name] = {"select": None}
        elif prop_type == "multi_select":
            properties_object[prop_name] = {"multi_select": []}
        elif prop_type == "date":
            properties_object[prop_name] = {"date": None}
        elif prop_type == "people":
            properties_object[prop_name] = {"people": []}
        elif prop_type == "files":
            properties_object[prop_name] = {"files": []}
        elif prop_type == "checkbox":
            properties_object[prop_name] = {"checkbox": False}
        elif prop_type == "url":
            properties_object[prop_name] = {"url": None}
        elif prop_type == "email":
            properties_object[prop_name] = {"email": None}
        elif prop_type == "phone_number":
            properties_object[prop_name] = {"phone_number": None}
        elif prop_type == "relation":
            properties_object[prop_name] = {"relation": []}
        elif prop_type == "status":
            properties_object[prop_name] = {"status": None}

    return properties_object
