"""
Security utilities for the Azure Orbital Space SDK.

This module provides input validation functions to prevent injection attacks
and ensure data integrity throughout the SDK.
"""

from .validation import (
    validate_docker_image_name,
    validate_docker_tag,
    validate_file_path,
    validate_filename,
    validate_helm_parameter,
    validate_helm_value,
    validate_kubernetes_namespace,
    validate_kubernetes_resource_name,
    validate_identifier,
    sanitize_input,
    sanitize_shell_argument,
    is_safe_filename,
    contains_shell_metacharacters,
    contains_path_traversal,
    is_within_directory,
    is_alphanumeric,
    is_alphanumeric_with_dash,
    is_valid_identifier,
)

__all__ = [
    'validate_docker_image_name',
    'validate_docker_tag',
    'validate_file_path',
    'validate_filename',
    'validate_helm_parameter',
    'validate_helm_value',
    'validate_kubernetes_namespace',
    'validate_kubernetes_resource_name',
    'validate_identifier',
    'sanitize_input',
    'sanitize_shell_argument',
    'is_safe_filename',
    'contains_shell_metacharacters',
    'contains_path_traversal',
    'is_within_directory',
    'is_alphanumeric',
    'is_alphanumeric_with_dash',
    'is_valid_identifier',
]
