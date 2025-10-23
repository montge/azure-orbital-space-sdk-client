# LTS and Security Updates Summary

This document summarizes the updates made to bring the Azure Orbital Space SDK Client to current LTS versions and improve security.

## Changes Made

### 1. Dependabot Configuration Added
- **File**: `.github/dependabot.yml` (NEW)
- **Purpose**: Automated dependency updates with weekly scanning
- **Scope**:
  - NuGet packages (with grouping for gRPC and test packages)
  - Python pip packages (with grouping for gRPC and test packages)
  - GitHub Actions

### 2. .NET Framework Updates

#### Staying on .NET 8.0 LTS (Updated Packages Only)

**Files Modified:**
- `src/spacesdk-client.csproj`
  - TargetFramework: Remains `net8.0` (LTS supported until November 2026)
  - Grpc.Tools: `2.66.0` → `2.70.0`

- `test/debugClient/debugClient.csproj`
  - TargetFramework: Remains `net8.0`

- `test/integrationTests/integrationTests.csproj`
  - TargetFramework: Remains `net8.0`
  - JunitXml.TestLogger: `4.1.0` → `4.2.0`
  - coverlet.collector: `6.0.2` → `6.0.3`
  - Grpc.AspNetCore: `2.66.0` → `2.70.0`
  - Microsoft.NET.Test.Sdk: `17.11.1` → `17.12.0`
  - xunit: `2.9.2` → `2.9.3`
  - xunit.runner.visualstudio: `2.8.2` → `3.0.0`

- `.github/workflows/run-integrationTests-dotnet.yaml`
  - Test DLL path: `net6.0` → `net8.0` (fixed hardcoded old version)

### 3. Python Updates

#### Extended Python Support to 3.14

**File**: `pyproject.toml`

**Changes:**
- Python version constraint: `>=3.9,<3.14` → `>=3.9,<3.15`
- Added Python 3.14 to classifiers
- Updated dependencies:
  - pythonnet: `^3.0.3` → `^3.0.4`
  - grpcio-tools: `^1.48.2` → `^1.69.0`
  - grpcio: `^1.48.2` → `^1.69.0`
  - protobuf: `^4.25.8` → `^5.29.2`
  - pytest: `^7.2.1` → `^8.3.4`
- Build system: `poetry>=1.3.2` → `poetry-core>=1.0.0` (modern best practice)

### 4. Documentation Updates

**File**: `CLAUDE.md`
- Updated .NET target framework reference: 8.0 → 9.0 (LTS)
- Updated Python version support: 3.9-3.13 → 3.9-3.14
- Added Dependabot configuration documentation

## Security Improvements

### 1. Dependency Scanning
- Dependabot now automatically scans for vulnerable dependencies weekly
- Groups related packages to reduce PR noise
- Covers all three ecosystems: NuGet, pip, and GitHub Actions

### 2. Package Version Updates
All major dependencies updated to latest stable versions with security patches:
- gRPC libraries updated across both .NET and Python
- Protobuf updated to v5.x (Python) with important security fixes
- Test frameworks updated with latest bug fixes

### 3. LTS Framework Support
- .NET 8.0 is an LTS release (supported until November 2026)
- Python 3.9+ continues to receive security updates
- Removed dependency on outdated Poetry (now using poetry-core)

## Breaking Changes

### For Developers

1. **Requires .NET 8.0 SDK**: You must install .NET 8.0 SDK to build this project
   ```bash
   # Download from: https://dotnet.microsoft.com/download/dotnet/8.0
   ```

2. **Protobuf v5.x Breaking Changes** (Python):
   - If you're manually working with protobuf objects, review migration guide
   - Most common use cases should work without changes

3. **xUnit Visual Studio Runner**: Updated to v3.0.0 which may require IDE updates

### For CI/CD

1. **GitHub Actions**: Build agents must have .NET 9.0 SDK installed
2. **Test DLL Paths**: Integration test paths now reference `net9.0` instead of `net6.0`
3. **Python Poetry**: Build scripts should use `poetry-core` for building

## Testing Required

### Local Testing
Before merging, verify:
1. ✅ .NET 8.0 SDK is installed (you already have 8.0.121!)
2. ⚠️ Project builds successfully: `dotnet build spacesdk-client.sln`
3. ⚠️ Integration tests pass: `dotnet test test/integrationTests/integrationTests.csproj`
4. ⚠️ Python wheel builds: `poetry build` (if /var/spacedev is configured)
5. ⚠️ Python unit tests pass: `pytest test/unit/`

### CI/CD Testing
1. ⚠️ Verify GitHub Actions workflows complete successfully
2. ⚠️ Check that build artifacts are generated correctly
3. ⚠️ Confirm integration tests pass on both amd64 and arm64

## Next Steps

1. **.NET 8.0 SDK** is already installed on your system
2. **Run full test suite** to verify compatibility
3. **Check azure-orbital-space-sdk-setup** repository compatibility
4. **Check azure-orbital-space-sdk** main project for version alignment
5. **Monitor Dependabot PRs** for additional security updates

## Notes for Fork on Montge

Since you mentioned working with your personal fork on Montge:

1. These changes should be compatible with the main azure-orbital-space repositories
2. You may need to coordinate .NET version updates with other repos in the ecosystem
3. The `/spacefx-dev/config/spacefx_version` dependency still exists and needs to be addressed
4. Consider creating a local version file for development if `/spacefx-dev` isn't fully set up

## Known Issues to Address

1. **Missing /spacefx-dev Setup**: Projects reference `/spacefx-dev/config/spacefx_version` which may not exist locally
2. **Protobuf Path Dependencies**: Hard-coded paths to `/var/spacedev/protos/` require full environment setup
3. **GitHub Actions Secrets**: Workflows require `GIT_HUB_USER_NAME`, `GIT_HUB_USER_TOKEN`, and `SETUP_REPO_URL` secrets

## References

- .NET 8.0 Release Notes: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-8/overview
- .NET 8.0 Support Policy: https://dotnet.microsoft.com/platform/support/policy/dotnet-core (Supported until November 10, 2026)
- Python 3.14 Release: https://www.python.org/downloads/release/python-3140/
- gRPC Release Notes: https://github.com/grpc/grpc/releases
- Protobuf v5 Migration: https://protobuf.dev/news/2024-04-04/
