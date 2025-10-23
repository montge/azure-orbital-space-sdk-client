# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository provides dual-language client libraries (DotNet and Python) for Payload Applications to interact with the Microsoft Azure Orbital Space SDK. The Python client uses PythonNet to wrap the .NET implementation, loading compiled .NET DLLs at runtime.

## Build Commands

### Prerequisites
The build system requires `/var/spacedev` to be provisioned:
```bash
# Clone and run setup from azure-orbital-space-sdk-setup
git clone https://github.com/microsoft/azure-orbital-space-sdk-setup
cd azure-orbital-space-sdk-setup
bash ./.vscode/copy_to_spacedev.sh
cd -
```

### Build DotNet Client Library
```bash
/var/spacedev/build/dotnet/build_app.sh \
    --repo-dir ${PWD} \
    --app-project src/spacesdk-client.csproj \
    --nuget-project src/spacesdk-client.csproj \
    --output-dir /var/spacedev/tmp/spacesdk-client \
    --app-version 0.11.0 \
    --no-container-build
```

### Build Python Client Wheel
```bash
/var/spacedev/build/python/build_app.sh \
    --repo-dir ${PWD} \
    --app-project spacefx \
    --output-dir /var/spacedev/tmp/spacesdk-client \
    --app-version 0.11.0 \
    --no-container-build
```

### Build Within Solution
```bash
# Build main client library
dotnet build src/spacesdk-client.csproj

# Build integration tests
dotnet build test/integrationTests/integrationTests.csproj

# Build debug client
dotnet build test/debugClient/debugClient.csproj

# Build entire solution
dotnet build spacesdk-client.sln
```

## Testing

### DotNet Integration Tests
```bash
# Run all integration tests
dotnet test test/integrationTests/integrationTests.csproj --verbosity detailed

# Run with JUnit output
dotnet test test/integrationTests/integrationTests.csproj \
    --logger "junit;LogFileName=test-results.xml"
```

### Python Unit Tests
```bash
# Run security validation tests
pytest test/unit/

# Run specific test file
pytest test/unit/security/test_validation.py
```

### Python Integration Tests
Integration tests use the debug shim deployment:
```bash
/spacefx-dev/debugShim-deploy.sh \
    --debug_shim spacesdk-client \
    --python_file test/integrationTests_python/integrationTest.py \
    --disable_plugin_configs \
    --port 5678
```

### Debug Clients
```bash
# DotNet debug client
dotnet run --project test/debugClient/debugClient.csproj

# Python debug client
python test/debugClient_python/debugClient.py
```

## Architecture

### DotNet Client (`src/`)
- **Target Framework**: .NET 8.0 (LTS)
- **Main Entry**: `Client.cs` - Handles gRPC messaging hub, listens on port 50051
- **Host Services**: `HostServices/` - Service wrappers for Sensor, Position, Link, Logging
- **Configuration**: Loads from `SPACEFX_SECRET_DIR/config/appsettings.json` with local overrides
- **Dependencies**: `Microsoft.Azure.SpaceSDK.Core` (version from `/spacefx-dev/config/spacefx_version`)
- **Protobuf Compilation**: gRPC services generated from `/var/spacedev/protos/spacefx/protos/`

### Python Client (`spacefx/`)
- **Bridge Technology**: Uses PythonNet (`pythonnet ^3.0.3`) to load .NET DLLs
- **DLL Loading**: `_sdk_client.py` dynamically loads compiled .NET assemblies from `spacefx/spacefxClient/`
- **API Wrappers**: Pythonic interfaces around .NET types
- **Python Versions**: 3.9 - 3.14 supported
- **Build System**: Poetry-based (`pyproject.toml`)
- **Security Module**: `spacefx/security/validation.py` provides comprehensive input validation (Docker, K8s, Helm, file paths, shell arguments)

### Request/Response Pattern
All host service interactions follow this pattern:
1. Generate unique tracking ID and correlation ID
2. Wait for target service to come online
3. Send request via `Client.DirectToApp()`
4. Register event handler for response
5. Poll for response with configurable timeout
6. Raise `TimeoutException` if no response received

### Message Flow
- Events dispatched asynchronously via `Task.Factory.StartNew()`
- Response validation by matching `TrackingId`
- Python receives sensor data as byte arrays (protobuf)
- Event types: `LogMessageResponseEvent`, `SensorDataEvent`, `PositionResponseEvent`, etc.

## Configuration

### Version Management
Current version: **0.11.0** (defined in `pyproject.toml` and used in build scripts)

### Protobuf Sources
Client library references protobufs from shared location:
- Position: `/var/spacedev/protos/spacefx/protos/position/Position.proto`
- Sensor: `/var/spacedev/protos/spacefx/protos/sensor/Sensor.proto`
- Link: `/var/spacedev/protos/spacefx/protos/link/Link.proto`

### Dependency Management
Dependabot is configured to automatically check for updates weekly:
- NuGet packages (with grouping for gRPC and test packages)
- Python pip packages (with grouping for gRPC and test packages)
- GitHub Actions

### appsettings.json Loading
Configuration cascade (in order of precedence):
1. `appsettings.{DOTNET_ENVIRONMENT}.json` (local override)
2. `appsettings.json` (local)
3. `{SPACEFX_SECRET_DIR}/config/appsettings.json` (default)

## Build Artifacts

### Outputs
- **NuGet Package**: `Microsoft.Azure.SpaceSDK.Client.{version}.nupkg`
  - Location: `/var/spacedev/nuget/client/`
- **Python Wheel**: `microsoftazurespacefx-{version}-py3-none-any.whl`
  - Location: `/var/spacedev/wheel/microsoftazurespacefx/`

### Artifact Publishing
```bash
# Push NuGet package
/var/spacedev/build/push_build_artifact.sh \
    --artifact /var/spacedev/nuget/client/Microsoft.Azure.SpaceSDK.Client.0.11.0.nupkg \
    --annotation-config azure-orbital-space-sdk-client.yaml \
    --architecture amd64 \
    --artifact-version 0.11.0

# Push Python wheel
/var/spacedev/build/push_build_artifact.sh \
    --artifact /var/spacedev/wheel/microsoftazurespacefx/microsoftazurespacefx-0.11.0-py3-none-any.whl \
    --annotation-config azure-orbital-space-sdk-client.yaml \
    --architecture amd64 \
    --artifact-version 0.11.0
```

## Development Environment

### Devcontainer Support
The repository includes `.devcontainer/` configuration for containerized development with the SpaceSDK environment pre-configured.

### CI/CD Workflows
- `.github/workflows/test-spacefx-client-dotnet.yaml` - DotNet tests (amd64 + arm64)
- `.github/workflows/test-spacefx-client-python.yaml` - Python tests (amd64 + arm64)
- `.github/workflows/spacefx-client-build.yaml` - Build pipeline
- Integration tests run within devcontainer using k3s deployment

## Key Implementation Details

### Python-DotNet Interop
The Python client does NOT reimplement the SDK - it wraps the compiled .NET DLLs. During the Python build:
1. DotNet client is compiled to DLLs
2. DLLs are copied to `spacefx/spacefxClient/`
3. Python wheel includes these DLLs
4. At runtime, `_sdk_client.py` uses PythonNet to load .NET assemblies

This architecture ensures feature parity between Python and DotNet clients.

### Security Validation
The `spacefx/security/validation.py` module provides whitelist-based input validation:
- Docker image/tag validation
- Kubernetes resource name validation
- Helm parameter validation
- Path traversal prevention
- Shell metacharacter detection
- Length constraints on all inputs

Use these validators when accepting external input before passing to system commands or APIs.

## Common Pitfalls

### Missing /var/spacedev
Many operations fail if `/var/spacedev` is not properly provisioned. Always run the setup script from `azure-orbital-space-sdk-setup` first.

### Version Synchronization
The version string appears in multiple locations. When updating versions, ensure consistency across:
- `pyproject.toml` (`tool.poetry.version`)
- Build script commands (`--app-version`)
- README examples

### Protobuf Path Dependencies
The `.csproj` file hard-codes paths to protobuf files in `/var/spacedev/protos/`. These must exist for builds to succeed.

### SpaceSDK Core Version
The DotNet projects read the SpaceSDK Core version from `/spacefx-dev/config/spacefx_version`. This file must exist and contain a valid version string.
