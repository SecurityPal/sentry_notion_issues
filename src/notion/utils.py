from typing import Any


def initialize_empty_properties(property_schema: dict[str, Any]) -> dict[str, Any]:
    """Initialize empty property values for all property types in the schema.

    Args:
        property_schema: The database property schema

    Returns:
        Dictionary of property ID to empty property value

    """
    properties_object: dict[str, Any] = {}

    for prop in property_schema.values():
        prop_type = getattr(prop, "type", None)
        if not prop_type:
            continue

        if prop_type == "title":
            # Skip title as it's typically set explicitly
            pass
        elif prop_type == "rich_text":
            properties_object[prop.id] = {"rich_text": []}
        elif prop_type == "number":
            properties_object[prop.id] = {"number": None}
        elif prop_type == "select":
            properties_object[prop.id] = {"select": None}
        elif prop_type == "multi_select":
            properties_object[prop.id] = {"multi_select": []}
        elif prop_type == "date":
            properties_object[prop.id] = {"date": None}
        elif prop_type == "people":
            properties_object[prop.id] = {"people": []}
        elif prop_type == "files":
            properties_object[prop.id] = {"files": []}
        elif prop_type == "checkbox":
            properties_object[prop.id] = {"checkbox": False}
        elif prop_type == "url":
            properties_object[prop.id] = {"url": None}
        elif prop_type == "email":
            properties_object[prop.id] = {"email": None}
        elif prop_type == "phone_number":
            properties_object[prop.id] = {"phone_number": None}
        elif prop_type == "relation":
            properties_object[prop.id] = {"relation": []}
        elif prop_type == "status":
            properties_object[prop.id] = {"status": None}

    return properties_object
