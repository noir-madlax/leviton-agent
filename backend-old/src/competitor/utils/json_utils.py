"""
JSON processing utilities for LLM response handling.

Provides:
- JSON extraction from LLM responses
- JSON validation and structure checking
- Error handling for malformed JSON
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union


def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON from LLM response, handling various formats
    
    Args:
        response_text: Raw LLM response text
        
    Returns:
        Extracted JSON string
        
    Raises:
        ValueError: If no valid JSON found
    """
    # Look for JSON in markdown code blocks
    json_code_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    matches = re.findall(json_code_pattern, response_text, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Look for standalone JSON objects
    # Find the first { and try to find its matching }
    start_idx = response_text.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in response")
    
    # Count braces to find the matching closing brace
    brace_count = 0
    end_idx = start_idx
    
    for i in range(start_idx, len(response_text)):
        if response_text[i] == '{':
            brace_count += 1
        elif response_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
    
    if brace_count != 0:
        # Fallback to simple approach
        end_idx = response_text.rfind('}')
        if end_idx <= start_idx:
            raise ValueError("No complete JSON object found")
    
    return response_text[start_idx:end_idx + 1].strip()


def validate_json_structure(json_data: Any, required_keys: List[str], 
                          optional_keys: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate JSON structure against required and optional keys
    
    Args:
        json_data: Parsed JSON data
        required_keys: List of required top-level keys
        optional_keys: List of optional top-level keys
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(json_data, dict):
        return False, "JSON must be a dictionary/object"
    
    # Check required keys
    missing_keys = []
    for key in required_keys:
        if key not in json_data:
            missing_keys.append(key)
    
    if missing_keys:
        return False, f"Missing required keys: {missing_keys}"
    
    # Check for unexpected keys if optional_keys is provided
    if optional_keys is not None:
        allowed_keys = set(required_keys + optional_keys)
        unexpected_keys = set(json_data.keys()) - allowed_keys
        if unexpected_keys:
            return False, f"Unexpected keys found: {list(unexpected_keys)}"
    
    return True, ""


def safe_json_loads(json_string: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Safely load JSON string with error handling
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Tuple of (success, result_or_error_message)
    """
    try:
        result = json.loads(json_string)
        return True, result
    except json.JSONDecodeError as e:
        return False, f"JSON decode error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def extract_and_validate_json(response_text: str, 
                             required_keys: List[str],
                             optional_keys: Optional[List[str]] = None) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Extract and validate JSON from LLM response in one step
    
    Args:
        response_text: Raw LLM response text
        required_keys: List of required top-level keys
        optional_keys: List of optional top-level keys
        
    Returns:
        Tuple of (success, result_or_error_message)
    """
    try:
        # Extract JSON
        json_string = extract_json_from_response(response_text)
        
        # Parse JSON
        success, result = safe_json_loads(json_string)
        if not success:
            return False, result
        
        # Validate structure
        is_valid, error_msg = validate_json_structure(result, required_keys, optional_keys)
        if not is_valid:
            return False, error_msg
        
        return True, result
        
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error during JSON extraction: {e}"


def format_json_for_display(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format JSON data for display with proper indentation
    
    Args:
        data: JSON data to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def merge_json_objects(*json_objects: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple JSON objects, with later objects overriding earlier ones
    
    Args:
        json_objects: Variable number of JSON objects to merge
        
    Returns:
        Merged JSON object
    """
    result = {}
    for obj in json_objects:
        if isinstance(obj, dict):
            result.update(obj)
    return result


def extract_nested_value(json_data: Dict[str, Any], key_path: str, 
                        separator: str = ".") -> Optional[Any]:
    """
    Extract nested value from JSON using dot notation
    
    Args:
        json_data: JSON data to search
        key_path: Path to the value (e.g., "section.subsection.key")
        separator: Separator character for path components
        
    Returns:
        Extracted value or None if not found
    """
    keys = key_path.split(separator)
    current = json_data
    
    try:
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    except (TypeError, KeyError):
        return None 