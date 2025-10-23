"""
Unit tests for validation module.

Tests cover valid inputs, invalid inputs (injection attempts),
edge cases, and boundary conditions.
"""

import os
import tempfile
import pytest
from pathlib import Path

from spacefx.security.validation import (
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
    ALPHANUMERIC_CHARS,
    LOWERCASE_ALPHANUMERIC,
)


class TestDockerImageValidation:
    """Tests for Docker image name validation."""

    @pytest.mark.parametrize("image_name,expected", [
        ("myapp", True),
        ("registry.io/myapp", True),
        ("my-app_v1", True),
        ("registry.io/namespace/myapp", True),
        ("app123", True),
        ("a", True),
        ("MYAPP", False),  # Uppercase not allowed
        ("my..app", False),  # Double separator
        ("my app", False),  # Space not allowed
        (".myapp", False),  # Starts with separator
        ("myapp.", False),  # Ends with separator
        ("my/app/", False),  # Ends with separator
        ("my|app", False),  # Invalid character
        ("my&app", False),  # Shell metacharacter
        ("", False),  # Empty
        ("   ", False),  # Whitespace only
    ])
    def test_validate_docker_image_name(self, image_name, expected):
        """Test Docker image name validation with various inputs."""
        assert validate_docker_image_name(image_name) == expected

    def test_validate_docker_image_name_null_raises_error(self):
        """Test that None input raises TypeError."""
        with pytest.raises(TypeError):
            validate_docker_image_name(None)

    def test_validate_docker_image_name_non_string_raises_error(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            validate_docker_image_name(123)

    def test_validate_docker_image_name_too_long(self):
        """Test that image names exceeding max length are rejected."""
        long_name = "a" * 256
        assert validate_docker_image_name(long_name) is False

    def test_validate_docker_image_name_max_length(self):
        """Test that image names at max length are accepted."""
        max_name = "a" * 255
        assert validate_docker_image_name(max_name) is True


class TestDockerTagValidation:
    """Tests for Docker tag validation."""

    @pytest.mark.parametrize("tag,expected", [
        ("latest", True),
        ("v1.0.0", True),
        ("sha-abc123", True),
        ("1.2.3-beta_1", True),
        ("a", True),
        ("A", True),
        ("invalid tag", False),  # Space not allowed
        ("tag|pipe", False),  # Invalid character
        ("tag&amp", False),  # Shell metacharacter
        ("", False),  # Empty
        ("   ", False),  # Whitespace only
    ])
    def test_validate_docker_tag(self, tag, expected):
        """Test Docker tag validation with various inputs."""
        assert validate_docker_tag(tag) == expected

    def test_validate_docker_tag_null_raises_error(self):
        """Test that None input raises TypeError."""
        with pytest.raises(TypeError):
            validate_docker_tag(None)

    def test_validate_docker_tag_too_long(self):
        """Test that tags exceeding max length are rejected."""
        long_tag = "a" * 129
        assert validate_docker_tag(long_tag) is False

    def test_validate_docker_tag_max_length(self):
        """Test that tags at max length are accepted."""
        max_tag = "a" * 128
        assert validate_docker_tag(max_tag) is True


class TestFilePathValidation:
    """Tests for file path validation."""

    def test_validate_file_path_valid_within_base(self):
        """Test that valid paths within base directory are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_path = os.path.join(tmpdir, "subfolder", "file.txt")
            assert validate_file_path(valid_path, tmpdir) is True

    @pytest.mark.parametrize("malicious_path", [
        "../../../etc/passwd",
        "../../etc/passwd",
        "test/../../etc/passwd",
        "./../etc/passwd",
    ])
    def test_validate_file_path_traversal_attempts(self, malicious_path):
        """Test that path traversal attempts are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            full_path = os.path.join(tmpdir, malicious_path)
            assert validate_file_path(full_path, tmpdir) is False

    def test_validate_file_path_null_byte_injection(self):
        """Test that null byte injection is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            malicious_path = os.path.join(tmpdir, "file.txt\x00.exe")
            assert validate_file_path(malicious_path, tmpdir) is False

    def test_validate_file_path_null_inputs_raise_error(self):
        """Test that None inputs raise TypeError."""
        with pytest.raises(TypeError):
            validate_file_path(None, "/base")
        with pytest.raises(TypeError):
            validate_file_path("/path", None)

    def test_validate_file_path_too_long(self):
        """Test that paths exceeding max length are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            long_path = os.path.join(tmpdir, "a" * 4097)
            assert validate_file_path(long_path, tmpdir) is False


class TestFilenameValidation:
    """Tests for filename validation."""

    @pytest.mark.parametrize("filename,expected", [
        ("config.json", True),
        ("data_file-v1.txt", True),
        ("file123.log", True),
        ("a.b", True),
        ("file", True),
        ("../etc/passwd", False),  # Path separator
        ("file/name.txt", False),  # Path separator
        ("file<name.txt", False),  # Invalid character
        ("file>name.txt", False),  # Invalid character
        ("file|name.txt", False),  # Shell metacharacter
        ("CON", False),  # Windows reserved name
        ("PRN", False),  # Windows reserved name
        ("CON.txt", False),  # Windows reserved name with extension
        ("", False),  # Empty
        ("   ", False),  # Whitespace only
    ])
    def test_validate_filename(self, filename, expected):
        """Test filename validation with various inputs."""
        assert validate_filename(filename) == expected

    def test_validate_filename_null_raises_error(self):
        """Test that None input raises TypeError."""
        with pytest.raises(TypeError):
            validate_filename(None)

    def test_validate_filename_too_long(self):
        """Test that filenames exceeding max length are rejected."""
        long_filename = "a" * 256 + ".txt"
        assert validate_filename(long_filename) is False

    def test_is_safe_filename_alias(self):
        """Test that is_safe_filename is an alias for validate_filename."""
        assert is_safe_filename("config.json") is True
        assert is_safe_filename("../passwd") is False


class TestIsWithinDirectory:
    """Tests for directory boundary checking."""

    def test_is_within_directory_valid_path(self):
        """Test that valid paths within base are detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_path = os.path.join(tmpdir, "subfolder", "file.txt")
            assert is_within_directory(valid_path, tmpdir) is True

    def test_is_within_directory_outside_path(self):
        """Test that paths outside base are detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as other_dir:
                outside_path = os.path.join(other_dir, "file.txt")
                assert is_within_directory(outside_path, tmpdir) is False

    def test_is_within_directory_null_raises_error(self):
        """Test that None inputs raise TypeError."""
        with pytest.raises(TypeError):
            is_within_directory(None, "/base")
        with pytest.raises(TypeError):
            is_within_directory("/path", None)


class TestContainsPathTraversal:
    """Tests for path traversal detection."""

    @pytest.mark.parametrize("path,expected", [
        ("../etc/passwd", True),
        ("safe/path/file.txt", False),
        ("%2e%2e/passwd", True),  # URL encoded
        ("../../passwd", True),
        ("/..", True),
        (".\\passwd", True),
        ("normal_file.txt", False),
    ])
    def test_contains_path_traversal(self, path, expected):
        """Test path traversal detection with various inputs."""
        assert contains_path_traversal(path) == expected

    def test_contains_path_traversal_null_raises_error(self):
        """Test that None input raises TypeError."""
        with pytest.raises(TypeError):
            contains_path_traversal(None)


class TestHelmValidation:
    """Tests for Helm parameter and value validation."""

    @pytest.mark.parametrize("parameter,expected", [
        ("app.replicas", True),
        ("config_name", True),
        ("namespace-name", True),
        ("simple", True),
        ("a.b.c.d", True),
        ("invalid param", False),  # Space
        ("param|pipe", False),  # Invalid character
        ("", False),  # Empty
    ])
    def test_validate_helm_parameter(self, parameter, expected):
        """Test Helm parameter validation with various inputs."""
        assert validate_helm_parameter(parameter) == expected

    @pytest.mark.parametrize("value,expected", [
        ("value123", True),
        ("path/to/resource", True),
        ("http://example.com", True),
        ("simple-value", True),
        ("value with spaces", False),  # Spaces not allowed
        ("value|pipe", False),  # Invalid character
        ("", False),  # Empty
    ])
    def test_validate_helm_value(self, value, expected):
        """Test Helm value validation with various inputs."""
        assert validate_helm_value(value) == expected

    def test_validate_helm_parameter_too_long(self):
        """Test that parameters exceeding max length are rejected."""
        long_param = "a" * 256
        assert validate_helm_parameter(long_param) is False

    def test_validate_helm_value_too_long(self):
        """Test that values exceeding max length are rejected."""
        long_value = "a" * 1025
        assert validate_helm_value(long_value) is False


class TestKubernetesValidation:
    """Tests for Kubernetes resource validation."""

    @pytest.mark.parametrize("namespace,expected", [
        ("default", True),
        ("my-namespace", True),
        ("app123", True),
        ("a", True),
        ("abc-def-ghi", True),
        ("INVALID", False),  # Uppercase
        ("-invalid", False),  # Starts with hyphen
        ("invalid-", False),  # Ends with hyphen
        ("in valid", False),  # Space
        ("in_valid", False),  # Underscore
        ("in.valid", False),  # Dot
        ("", False),  # Empty
    ])
    def test_validate_kubernetes_namespace(self, namespace, expected):
        """Test Kubernetes namespace validation with various inputs."""
        assert validate_kubernetes_namespace(namespace) == expected

    @pytest.mark.parametrize("resource,expected", [
        ("my-pod", True),
        ("service.v1", True),
        ("deployment-123", True),
        ("a", True),
        ("pod.svc.cluster.local", True),
        ("INVALID", False),  # Uppercase
        ("-invalid", False),  # Starts with hyphen
        ("invalid-", False),  # Ends with hyphen
        (".invalid", False),  # Starts with dot
        ("invalid.", False),  # Ends with dot
        ("in valid", False),  # Space
        ("", False),  # Empty
    ])
    def test_validate_kubernetes_resource_name(self, resource, expected):
        """Test Kubernetes resource name validation with various inputs."""
        assert validate_kubernetes_resource_name(resource) == expected

    def test_validate_kubernetes_namespace_too_long(self):
        """Test that namespaces exceeding max length are rejected."""
        long_name = "a" * 64
        assert validate_kubernetes_namespace(long_name) is False

    def test_validate_kubernetes_resource_name_too_long(self):
        """Test that resource names exceeding max length are rejected."""
        long_name = "a" * 254
        assert validate_kubernetes_resource_name(long_name) is False


class TestShellSecurity:
    """Tests for shell security functions."""

    @pytest.mark.parametrize("input_str,expected", [
        ("safe-filename.txt", False),
        ("file123", False),
        ("file.txt && rm -rf /", True),  # Command injection
        ("file | grep pattern", True),  # Pipe
        ("file; cat /etc/passwd", True),  # Semicolon
        ("file$(whoami)", True),  # Command substitution
        ("file`whoami`", True),  # Command substitution
        ("file&background", True),  # Background operator
        ("file<input", True),  # Redirection
        ("file>output", True),  # Redirection
        ("file*wildcard", True),  # Wildcard
        ("file?wildcard", True),  # Wildcard
        ("file[0-9]", True),  # Character class
        ("file{a,b}", True),  # Brace expansion
    ])
    def test_contains_shell_metacharacters(self, input_str, expected):
        """Test shell metacharacter detection with various inputs."""
        assert contains_shell_metacharacters(input_str) == expected

    def test_contains_shell_metacharacters_null_raises_error(self):
        """Test that None input raises TypeError."""
        with pytest.raises(TypeError):
            contains_shell_metacharacters(None)

    def test_sanitize_shell_argument_normal_input(self):
        """Test that normal input is properly quoted."""
        result = sanitize_shell_argument("safe-file.txt")
        assert result == "'safe-file.txt'"

    def test_sanitize_shell_argument_with_quotes(self):
        """Test that single quotes are properly escaped."""
        result = sanitize_shell_argument("file'with'quotes")
        assert result.startswith("'")
        assert result.endswith("'")
        assert "\\'" in result or "'\\''" in result

    def test_sanitize_shell_argument_empty(self):
        """Test that empty input returns empty quotes."""
        result = sanitize_shell_argument("")
        assert result == "''"

    def test_sanitize_shell_argument_null_raises_error(self):
        """Test that None input raises TypeError."""
        with pytest.raises(TypeError):
            sanitize_shell_argument(None)


class TestIdentifierValidation:
    """Tests for identifier validation."""

    @pytest.mark.parametrize("identifier,expected", [
        ("myVar", True),
        ("_internal", True),
        ("value123", True),
        ("_", True),
        ("a", True),
        ("camelCase", True),
        ("snake_case", True),
        ("PascalCase", True),
        ("123invalid", False),  # Starts with number
        ("my-var", False),  # Hyphen not allowed
        ("my var", False),  # Space not allowed
        ("my.var", False),  # Dot not allowed
        ("", False),  # Empty
    ])
    def test_validate_identifier(self, identifier, expected):
        """Test identifier validation with various inputs."""
        assert validate_identifier(identifier) == expected

    def test_validate_identifier_too_long(self):
        """Test that identifiers exceeding max length are rejected."""
        long_identifier = "a" + "b" * 255
        assert validate_identifier(long_identifier) is False

    def test_is_valid_identifier_alias(self):
        """Test that is_valid_identifier is an alias."""
        assert is_valid_identifier("myVariable") is True
        assert is_valid_identifier("123invalid") is False


class TestPatternMatching:
    """Tests for pattern matching helper functions."""

    @pytest.mark.parametrize("input_str,expected", [
        ("abc123", True),
        ("ABC123", True),
        ("abc-123", False),
        ("abc_123", False),
        ("", False),
        ("   ", False),
    ])
    def test_is_alphanumeric(self, input_str, expected):
        """Test alphanumeric checking."""
        assert is_alphanumeric(input_str) == expected

    @pytest.mark.parametrize("input_str,expected", [
        ("app-deployment-123", True),
        ("app123", True),
        ("APP-123", True),
        ("app_deployment", False),
        ("app.deployment", False),
        ("", False),
    ])
    def test_is_alphanumeric_with_dash(self, input_str, expected):
        """Test alphanumeric with dash checking."""
        assert is_alphanumeric_with_dash(input_str) == expected


class TestSanitization:
    """Tests for input sanitization."""

    def test_sanitize_input_removes_disallowed(self):
        """Test that disallowed characters are removed."""
        result = sanitize_input("abc-123!@#", ALPHANUMERIC_CHARS)
        assert result == "abc123"

    def test_sanitize_input_allowed_only_unchanged(self):
        """Test that input with only allowed characters is unchanged."""
        input_str = "abc123"
        result = sanitize_input(input_str, ALPHANUMERIC_CHARS)
        assert result == input_str

    def test_sanitize_input_no_allowed_chars(self):
        """Test that input with no allowed characters returns empty."""
        result = sanitize_input("!@#$%^&*()", ALPHANUMERIC_CHARS)
        assert result == ""

    def test_sanitize_input_null_raises_error(self):
        """Test that None inputs raise TypeError."""
        with pytest.raises(TypeError):
            sanitize_input(None, "abc")
        with pytest.raises(TypeError):
            sanitize_input("abc", None)

    def test_sanitize_input_preserves_order(self):
        """Test that character order is preserved."""
        result = sanitize_input("a1b2c3!@#", ALPHANUMERIC_CHARS)
        assert result == "a1b2c3"


class TestInjectionAttempts:
    """Tests for various injection attack attempts."""

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "$(rm -rf /)",  # Command injection
        "`whoami`",  # Command substitution
        "test\x00.txt",  # Null byte
    ])
    def test_docker_image_name_injection_attempts(self, malicious_input):
        """Test that various injection attempts are rejected."""
        assert validate_docker_image_name(malicious_input) is False

    @pytest.mark.parametrize("encoded_traversal", [
        "%2e%2e/passwd",  # URL encoded ..
        "%252e%252e/passwd",  # Double URL encoded
        "..%2fpasswd",
        "..%5cpasswd",
    ])
    def test_file_path_url_encoded_traversal(self, encoded_traversal):
        """Test that URL-encoded path traversal is detected."""
        assert contains_path_traversal(encoded_traversal) is True


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_validate_functions_with_unicode(self):
        """Test that unicode characters are properly handled."""
        # Most validators should reject unicode
        assert validate_docker_image_name("app-\u2603") is False  # Snowman
        assert validate_identifier("var_\u2603") is False

    def test_validate_functions_with_whitespace_variations(self):
        """Test various whitespace characters."""
        whitespace_chars = [" ", "\t", "\n", "\r", "\f", "\v"]
        for ws in whitespace_chars:
            assert validate_docker_image_name(f"app{ws}name") is False
            assert validate_identifier(f"var{ws}name") is False

    def test_empty_and_whitespace_handling(self):
        """Test that empty strings and whitespace are consistently rejected."""
        validators = [
            validate_docker_image_name,
            validate_docker_tag,
            validate_filename,
            validate_helm_parameter,
            validate_helm_value,
            validate_kubernetes_namespace,
            validate_kubernetes_resource_name,
            validate_identifier,
        ]

        for validator in validators:
            assert validator("") is False
            assert validator("   ") is False
            assert validator("\t") is False

    def test_boundary_lengths(self):
        """Test validation at boundary lengths."""
        # Docker image: 255 chars (valid), 256 chars (invalid)
        assert validate_docker_image_name("a" * 255) is True
        assert validate_docker_image_name("a" * 256) is False

        # Docker tag: 128 chars (valid), 129 chars (invalid)
        assert validate_docker_tag("a" * 128) is True
        assert validate_docker_tag("a" * 129) is False

        # K8s namespace: 63 chars (valid), 64 chars (invalid)
        assert validate_kubernetes_namespace("a" * 63) is True
        assert validate_kubernetes_namespace("a" * 64) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
