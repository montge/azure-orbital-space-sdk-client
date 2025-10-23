"""
Input validation functions to prevent injection attacks and ensure data integrity.

This module provides validation functions following a whitelist (allow-list) approach
for maximum security. All functions are designed to be thread-safe and performant.

Examples:
    Basic validation:
        >>> from spacefx.security import validate_docker_image_name
        >>> validate_docker_image_name("myapp")
        True
        >>> validate_docker_image_name("MY-APP")
        False

    Path validation:
        >>> from spacefx.security import is_within_directory
        >>> is_within_directory("/var/app/data/file.txt", "/var/app/data")
        True
        >>> is_within_directory("/var/app/../etc/passwd", "/var/app/data")
        False
"""

import os
import re
from pathlib import Path
from typing import Optional, Set
from urllib.parse import unquote

# Validation patterns
_DOCKER_IMAGE_NAME_PATTERN = re.compile(r'^[a-z0-9]+([._/-][a-z0-9]+)*$')
_DOCKER_TAG_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]{1,128}$')
_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
_HELM_PARAMETER_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
_HELM_VALUE_PATTERN = re.compile(r'^[a-zA-Z0-9._:/-]+$')
_K8S_NAMESPACE_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
_K8S_RESOURCE_NAME_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$')
_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
_ALPHANUMERIC_DASH_PATTERN = re.compile(r'^[a-zA-Z0-9-]+$')
_PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.|/\.|\\\\.')

# Dangerous characters and sequences
_SHELL_METACHARACTERS: Set[str] = set('|&;<>()$`\\"\'\\n\\r\\t*?[]{}!#~')
_PATH_TRAVERSAL_SEQUENCES = [
    '..',
    '/..',
    '.\\\\',
    '\\\\..',
    '..\\\\',
    '../',
    '%2e%2e',
    '%252e%252e',
    '..%2f',
    '..%5c',
]
_NULL_BYTE_SEQUENCES = ['\\0', '%00', '\\u0000']
_WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}

# Length constraints
_MAX_DOCKER_IMAGE_NAME_LENGTH = 255
_MAX_DOCKER_TAG_LENGTH = 128
_MAX_FILENAME_LENGTH = 255
_MAX_FILEPATH_LENGTH = 4096
_MAX_K8S_NAMESPACE_LENGTH = 63
_MAX_K8S_RESOURCE_NAME_LENGTH = 253
_MAX_HELM_PARAMETER_LENGTH = 255
_MAX_HELM_VALUE_LENGTH = 1024
_MAX_IDENTIFIER_LENGTH = 255

# Character sets
ALPHANUMERIC_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
ALPHANUMERIC_WITH_SEPARATORS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.'
LOWERCASE_ALPHANUMERIC = 'abcdefghijklmnopqrstuvwxyz0123456789'
NUMERIC_CHARS = '0123456789'
HEX_CHARS_LOWER = '0123456789abcdef'


# Docker validation functions

def validate_docker_image_name(image_name: str) -> bool:
    """
    Validate a Docker image name according to Docker naming conventions.

    Args:
        image_name: The Docker image name to validate (e.g., "registry.io/myapp").

    Returns:
        True if the image name is valid, False otherwise.

    Raises:
        TypeError: If image_name is not a string.

    Notes:
        Valid image names:
        - Must contain only lowercase alphanumeric characters and separators (., _, -, /)
        - Cannot exceed 255 characters
        - Cannot start or end with separator

    Examples:
        >>> validate_docker_image_name("myapp")
        True
        >>> validate_docker_image_name("registry.io/my-app")
        True
        >>> validate_docker_image_name("MYAPP")
        False
        >>> validate_docker_image_name("my..app")
        False
    """
    if not isinstance(image_name, str):
        raise TypeError(f"image_name must be a string, got {type(image_name).__name__}")

    if not image_name or image_name.isspace():
        return False

    if len(image_name) > _MAX_DOCKER_IMAGE_NAME_LENGTH:
        return False

    return bool(_DOCKER_IMAGE_NAME_PATTERN.match(image_name))


def validate_docker_tag(tag: str) -> bool:
    """
    Validate a Docker tag according to Docker tagging conventions.

    Args:
        tag: The Docker tag to validate (e.g., "latest", "v1.0.0").

    Returns:
        True if the tag is valid, False otherwise.

    Raises:
        TypeError: If tag is not a string.

    Notes:
        Valid tags:
        - Must contain only alphanumeric characters and separators (_, ., -)
        - Length between 1 and 128 characters

    Examples:
        >>> validate_docker_tag("latest")
        True
        >>> validate_docker_tag("v1.0.0")
        True
        >>> validate_docker_tag("sha-abc123")
        True
        >>> validate_docker_tag("invalid tag")
        False
    """
    if not isinstance(tag, str):
        raise TypeError(f"tag must be a string, got {type(tag).__name__}")

    if not tag or tag.isspace():
        return False

    return bool(_DOCKER_TAG_PATTERN.match(tag))


# File path validation functions

def validate_file_path(path: str, base_path: str) -> bool:
    """
    Validate a file path to prevent path traversal attacks.

    This function checks for:
    - Path traversal sequences (.., etc.)
    - Null byte injection
    - Ensures path resolves within base_path
    - Validates file name components

    Args:
        path: The file path to validate.
        base_path: The base directory that the path must stay within.

    Returns:
        True if the path is valid and within base_path, False otherwise.

    Raises:
        TypeError: If path or base_path is not a string.

    Examples:
        >>> validate_file_path("/var/app/data/file.txt", "/var/app/data")
        True
        >>> validate_file_path("/var/app/../etc/passwd", "/var/app/data")
        False
        >>> validate_file_path("../../etc/passwd", "/var/app/data")
        False
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be a string, got {type(path).__name__}")
    if not isinstance(base_path, str):
        raise TypeError(f"base_path must be a string, got {type(base_path).__name__}")

    if not path or path.isspace():
        return False

    if len(path) > _MAX_FILEPATH_LENGTH:
        return False

    # Check for null bytes
    for null_byte in _NULL_BYTE_SEQUENCES:
        if null_byte in path:
            return False

    # Check for path traversal
    if contains_path_traversal(path):
        return False

    # Verify path is within base directory
    return is_within_directory(path, base_path)


def validate_filename(filename: str) -> bool:
    """
    Validate a file name (without path) to ensure it contains only safe characters.

    Args:
        filename: The file name to validate.

    Returns:
        True if the filename is safe, False otherwise.

    Raises:
        TypeError: If filename is not a string.

    Notes:
        Valid file names:
        - Must contain only alphanumeric characters, underscores, dots, and hyphens
        - Cannot exceed 255 characters
        - Cannot be a Windows reserved name (CON, PRN, etc.)
        - Cannot contain path separators

    Examples:
        >>> validate_filename("config.json")
        True
        >>> validate_filename("data_file-v1.txt")
        True
        >>> validate_filename("../etc/passwd")
        False
        >>> validate_filename("CON")
        False
    """
    if not isinstance(filename, str):
        raise TypeError(f"filename must be a string, got {type(filename).__name__}")

    if not filename or filename.isspace():
        return False

    if len(filename) > _MAX_FILENAME_LENGTH:
        return False

    # Check for path separators
    if os.sep in filename or (os.altsep and os.altsep in filename):
        return False

    # Check pattern
    if not _FILENAME_PATTERN.match(filename):
        return False

    # Check for Windows reserved names
    base_name = os.path.splitext(filename)[0].upper()
    if base_name in _WINDOWS_RESERVED_NAMES:
        return False

    return True


def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe (alias for validate_filename).

    Args:
        filename: The filename to check.

    Returns:
        True if the filename is safe, False otherwise.

    Examples:
        >>> is_safe_filename("data.json")
        True
        >>> is_safe_filename("../passwd")
        False
    """
    return validate_filename(filename)


def is_within_directory(path: str, base_directory: str) -> bool:
    """
    Check if a path resolves to a location within the specified base directory.

    This function resolves symbolic links and relative paths before comparing.

    Args:
        path: The path to check.
        base_directory: The base directory that must contain the path.

    Returns:
        True if the path is within the base directory, False otherwise.

    Raises:
        TypeError: If path or base_directory is not a string.

    Examples:
        >>> is_within_directory("/var/app/data/file.txt", "/var/app/data")
        True
        >>> is_within_directory("/var/app/../etc/passwd", "/var/app")
        False
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be a string, got {type(path).__name__}")
    if not isinstance(base_directory, str):
        raise TypeError(f"base_directory must be a string, got {type(base_directory).__name__}")

    try:
        # Resolve to absolute paths
        full_path = os.path.abspath(os.path.expanduser(path))
        full_base = os.path.abspath(os.path.expanduser(base_directory))

        # Add trailing separator to base path
        if not full_base.endswith(os.sep):
            full_base += os.sep

        # Check if path starts with base
        return full_path.startswith(full_base)
    except (ValueError, OSError):
        # Invalid path
        return False


def contains_path_traversal(path: str) -> bool:
    """
    Check if a path contains path traversal sequences.

    Args:
        path: The path to check.

    Returns:
        True if path traversal sequences are detected, False otherwise.

    Raises:
        TypeError: If path is not a string.

    Notes:
        Detects:
        - Standard traversal: ".."
        - Path variations: "/..", ".\\\\", etc.
        - URL encoded: "%2e%2e", "%252e%252e", etc.

    Examples:
        >>> contains_path_traversal("../etc/passwd")
        True
        >>> contains_path_traversal("safe/path/file.txt")
        False
        >>> contains_path_traversal("%2e%2e/passwd")
        True
    """
    if not isinstance(path, str):
        raise TypeError(f"path must be a string, got {type(path).__name__}")

    # Check regex pattern
    if _PATH_TRAVERSAL_PATTERN.search(path):
        return True

    # Check known sequences (case-insensitive)
    path_lower = path.lower()
    for sequence in _PATH_TRAVERSAL_SEQUENCES:
        if sequence.lower() in path_lower:
            return True

    # Check URL-decoded version
    try:
        decoded = unquote(path)
        if decoded != path and _PATH_TRAVERSAL_PATTERN.search(decoded):
            return True
    except Exception:
        pass

    return False


# Helm validation functions

def validate_helm_parameter(parameter: str) -> bool:
    """
    Validate a Helm parameter name.

    Args:
        parameter: The parameter name to validate.

    Returns:
        True if the parameter is valid, False otherwise.

    Raises:
        TypeError: If parameter is not a string.

    Notes:
        Valid parameter names:
        - Must contain only alphanumeric characters, dots, underscores, and hyphens
        - Cannot exceed 255 characters

    Examples:
        >>> validate_helm_parameter("app.replicas")
        True
        >>> validate_helm_parameter("config_name")
        True
        >>> validate_helm_parameter("invalid param")
        False
    """
    if not isinstance(parameter, str):
        raise TypeError(f"parameter must be a string, got {type(parameter).__name__}")

    if not parameter or parameter.isspace():
        return False

    if len(parameter) > _MAX_HELM_PARAMETER_LENGTH:
        return False

    return bool(_HELM_PARAMETER_PATTERN.match(parameter))


def validate_helm_value(value: str) -> bool:
    """
    Validate a Helm value.

    Args:
        value: The value to validate.

    Returns:
        True if the value is valid, False otherwise.

    Raises:
        TypeError: If value is not a string.

    Notes:
        Valid values:
        - Must contain only alphanumeric and safe separators (., _, :, -, /)
        - Cannot exceed 1024 characters
        - Supports common formats like URLs and paths

    Examples:
        >>> validate_helm_value("value123")
        True
        >>> validate_helm_value("path/to/resource")
        True
        >>> validate_helm_value("value with spaces")
        False
    """
    if not isinstance(value, str):
        raise TypeError(f"value must be a string, got {type(value).__name__}")

    if not value or value.isspace():
        return False

    if len(value) > _MAX_HELM_VALUE_LENGTH:
        return False

    return bool(_HELM_VALUE_PATTERN.match(value))


# Kubernetes validation functions

def validate_kubernetes_namespace(namespace_name: str) -> bool:
    """
    Validate a Kubernetes namespace name.

    Args:
        namespace_name: The namespace name to validate.

    Returns:
        True if the namespace name is valid, False otherwise.

    Raises:
        TypeError: If namespace_name is not a string.

    Notes:
        Valid namespace names:
        - Must be lowercase alphanumeric or hyphens
        - Cannot start or end with hyphen
        - Must be between 1 and 63 characters

    Examples:
        >>> validate_kubernetes_namespace("default")
        True
        >>> validate_kubernetes_namespace("my-namespace")
        True
        >>> validate_kubernetes_namespace("INVALID")
        False
        >>> validate_kubernetes_namespace("-invalid")
        False
    """
    if not isinstance(namespace_name, str):
        raise TypeError(f"namespace_name must be a string, got {type(namespace_name).__name__}")

    if not namespace_name or namespace_name.isspace():
        return False

    if len(namespace_name) > _MAX_K8S_NAMESPACE_LENGTH:
        return False

    return bool(_K8S_NAMESPACE_PATTERN.match(namespace_name))


def validate_kubernetes_resource_name(resource_name: str) -> bool:
    """
    Validate a Kubernetes resource name (pod, service, deployment, etc.).

    Args:
        resource_name: The resource name to validate.

    Returns:
        True if the resource name is valid, False otherwise.

    Raises:
        TypeError: If resource_name is not a string.

    Notes:
        Valid resource names:
        - Must be lowercase alphanumeric, hyphens, or dots
        - Cannot start or end with hyphen or dot
        - Must be between 1 and 253 characters

    Examples:
        >>> validate_kubernetes_resource_name("my-pod")
        True
        >>> validate_kubernetes_resource_name("service.v1")
        True
        >>> validate_kubernetes_resource_name("INVALID")
        False
    """
    if not isinstance(resource_name, str):
        raise TypeError(f"resource_name must be a string, got {type(resource_name).__name__}")

    if not resource_name or resource_name.isspace():
        return False

    if len(resource_name) > _MAX_K8S_RESOURCE_NAME_LENGTH:
        return False

    return bool(_K8S_RESOURCE_NAME_PATTERN.match(resource_name))


# Shell security functions

def contains_shell_metacharacters(input_str: str) -> bool:
    """
    Check if a string contains shell metacharacters.

    Args:
        input_str: The string to check.

    Returns:
        True if shell metacharacters are present, False otherwise.

    Raises:
        TypeError: If input_str is not a string.

    Notes:
        Checks for: |, &, ;, <, >, (, ), $, `, \\, ", ', newlines, tabs, *, ?, [, ], {, }, !, #, ~

    Examples:
        >>> contains_shell_metacharacters("safe_filename.txt")
        False
        >>> contains_shell_metacharacters("file.txt && rm -rf /")
        True
        >>> contains_shell_metacharacters("file | grep pattern")
        True
    """
    if not isinstance(input_str, str):
        raise TypeError(f"input_str must be a string, got {type(input_str).__name__}")

    return any(char in _SHELL_METACHARACTERS for char in input_str)


def sanitize_shell_argument(argument: str) -> str:
    """
    Sanitize a string for safe use as a shell argument.

    IMPORTANT: This provides defense-in-depth but should NOT be relied upon
    as the sole protection against command injection. Always prefer:
    1. Using parameterized APIs instead of shell commands
    2. Validating input against a whitelist before sanitization
    3. Running commands with minimum required privileges

    Args:
        argument: The argument to sanitize.

    Returns:
        A sanitized version of the argument safe for shell execution.

    Raises:
        TypeError: If argument is not a string.

    Notes:
        This function wraps the argument in single quotes and escapes any
        single quotes within it. This works on both Unix and Windows (PowerShell).

    Examples:
        >>> sanitize_shell_argument("safe-file.txt")
        "'safe-file.txt'"
        >>> sanitize_shell_argument("file'with'quotes")
        "'file'\\\\''with'\\\\''quotes'"
    """
    if not isinstance(argument, str):
        raise TypeError(f"argument must be a string, got {type(argument).__name__}")

    if not argument:
        return "''"

    # Wrap in single quotes and escape any single quotes
    return f"'{argument.replace(\"'\", \"'\\\\''\")}'"


# General validation functions

def validate_identifier(identifier: str) -> bool:
    """
    Validate that a string is a valid identifier (variable name, etc.).

    Args:
        identifier: The identifier to validate.

    Returns:
        True if the identifier is valid, False otherwise.

    Raises:
        TypeError: If identifier is not a string.

    Notes:
        Valid identifiers:
        - Must start with letter or underscore
        - Can contain letters, numbers, and underscores
        - Cannot exceed 255 characters

    Examples:
        >>> validate_identifier("myVar")
        True
        >>> validate_identifier("_internal")
        True
        >>> validate_identifier("123invalid")
        False
    """
    if not isinstance(identifier, str):
        raise TypeError(f"identifier must be a string, got {type(identifier).__name__}")

    if not identifier or identifier.isspace():
        return False

    if len(identifier) > _MAX_IDENTIFIER_LENGTH:
        return False

    return bool(_IDENTIFIER_PATTERN.match(identifier))


def is_valid_identifier(input_str: str) -> bool:
    """
    Check if a string is a valid identifier (alias for validate_identifier).

    Args:
        input_str: The string to check.

    Returns:
        True if the string is a valid identifier, False otherwise.

    Examples:
        >>> is_valid_identifier("myVariable")
        True
        >>> is_valid_identifier("123invalid")
        False
    """
    return validate_identifier(input_str)


def is_alphanumeric(input_str: str) -> bool:
    """
    Check if a string contains only alphanumeric characters.

    Args:
        input_str: The string to check.

    Returns:
        True if the string is purely alphanumeric, False otherwise.

    Raises:
        TypeError: If input_str is not a string.

    Examples:
        >>> is_alphanumeric("abc123")
        True
        >>> is_alphanumeric("abc-123")
        False
        >>> is_alphanumeric("")
        False
    """
    if not isinstance(input_str, str):
        raise TypeError(f"input_str must be a string, got {type(input_str).__name__}")

    if not input_str or input_str.isspace():
        return False

    return input_str.isalnum()


def is_alphanumeric_with_dash(input_str: str) -> bool:
    """
    Check if a string contains only alphanumeric characters and hyphens.

    Args:
        input_str: The string to check.

    Returns:
        True if the string is alphanumeric with hyphens, False otherwise.

    Raises:
        TypeError: If input_str is not a string.

    Examples:
        >>> is_alphanumeric_with_dash("app-deployment-123")
        True
        >>> is_alphanumeric_with_dash("app_deployment")
        False
        >>> is_alphanumeric_with_dash("")
        False
    """
    if not isinstance(input_str, str):
        raise TypeError(f"input_str must be a string, got {type(input_str).__name__}")

    if not input_str or input_str.isspace():
        return False

    return bool(_ALPHANUMERIC_DASH_PATTERN.match(input_str))


def sanitize_input(input_str: str, allowed_chars: str) -> str:
    """
    Sanitize input by removing all characters not in the allowed set.

    Args:
        input_str: The input to sanitize.
        allowed_chars: String containing all allowed characters.

    Returns:
        The sanitized input containing only allowed characters.

    Raises:
        TypeError: If input_str or allowed_chars is not a string.

    Examples:
        >>> sanitize_input("abc-123!@#", ALPHANUMERIC_CHARS)
        'abc123'
        >>> sanitize_input("my_file.txt", LOWERCASE_ALPHANUMERIC)
        'myfiletxt'
    """
    if not isinstance(input_str, str):
        raise TypeError(f"input_str must be a string, got {type(input_str).__name__}")
    if not isinstance(allowed_chars, str):
        raise TypeError(f"allowed_chars must be a string, got {type(allowed_chars).__name__}")

    allowed_set = set(allowed_chars)
    return ''.join(char for char in input_str if char in allowed_set)
