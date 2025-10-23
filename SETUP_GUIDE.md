# Setup Guide for Azure Orbital Space SDK Client Development

This guide will help you set up your development environment to build and work with the Azure Orbital Space SDK Client.

## Prerequisites

- ✅ .NET 8.0 SDK (you have 8.0.121 installed)
- ✅ Python 3.9+ (you have 3.12.3 installed)
- ✅ Poetry for Python package management
- ✅ Git

## Step 1: Initialize /var/spacedev

The client library depends on files in `/var/spacedev` which come from the `azure-orbital-space-sdk-setup` repository.

You already have this repository cloned at: `../azure-orbital-space-sdk-setup`

Run the setup script:

```bash
cd ../azure-orbital-space-sdk-setup
bash ./.vscode/copy_to_spacedev.sh
```

This will create `/var/spacedev` with:
- Build scripts
- Protocol buffer definitions
- Configuration files (including `spacefx_version`)
- Certificates and deployment scripts

### Verify the Setup

```bash
# Check that the version file exists
cat /var/spacedev/config/spacefx_version
# Should output: 0.11.0

# Check that protobuf files exist
ls -la /var/spacedev/protos/spacefx/protos/
# Should show: position/, sensor/, link/, common/, deployment/
```

## Step 2: Build the Client Library

### Option A: Using the SpaceSDK Build Scripts

```bash
cd ../azure-orbital-space-sdk-client

# Build .NET client library
/var/spacedev/build/dotnet/build_app.sh \
    --repo-dir ${PWD} \
    --app-project src/spacesdk-client.csproj \
    --nuget-project src/spacesdk-client.csproj \
    --output-dir /var/spacedev/tmp/spacesdk-client \
    --app-version 0.11.0 \
    --no-container-build

# Build Python client wheel
/var/spacedev/build/python/build_app.sh \
    --repo-dir ${PWD} \
    --app-project spacefx \
    --output-dir /var/spacedev/tmp/spacesdk-client \
    --app-version 0.11.0 \
    --no-container-build
```

### Option B: Using Standard .NET Tools

```bash
cd ../azure-orbital-space-sdk-client

# Build the solution
dotnet build spacesdk-client.sln

# Run tests
dotnet test test/integrationTests/integrationTests.csproj
```

### Option C: Using Poetry for Python

```bash
cd ../azure-orbital-space-sdk-client

# Install dependencies
poetry install

# Run unit tests
pytest test/unit/

# Build Python wheel
poetry build
```

## Step 3: Understanding the Dependencies

### Critical Path Dependencies

Your `.csproj` files reference:

1. **SpaceSDK Core Version**:
   ```xml
   <PackageReference Include="Microsoft.Azure.SpaceSDK.Core"
       Version="$([System.IO.File]::ReadAllText('/spacefx-dev/config/spacefx_version'))" />
   ```
   - Reads from: `/var/spacedev/config/spacefx_version`
   - Contains: `0.11.0`

2. **Protocol Buffers**:
   ```xml
   <Protobuf Include="/var/spacedev/protos/spacefx/protos/position/Position.proto" ... />
   ```
   - Location: `/var/spacedev/protos/spacefx/protos/`
   - Files: `position/`, `sensor/`, `link/`

### Where These Come From

All these files are sourced from `azure-orbital-space-sdk-setup`:
- Protobuf definitions: `azure-orbital-space-sdk-setup/protos/spacefx/protos/`
- Version file: Created from `azure-orbital-space-sdk-setup/env/spacefx.env`
- Build scripts: `azure-orbital-space-sdk-setup/build/`

## Step 4: Working with Your Fork on Montge

Since you're working with a personal fork, you may want to adjust some paths:

### Option 1: Use Symbolic Links (Recommended)

If `/var/spacedev` doesn't suit your workflow, create a symlink:

```bash
# Create your own directory
sudo mkdir -p /home/e/Development/spacefx-dev

# Link it to /var/spacedev
sudo ln -s /home/e/Development/spacefx-dev /var/spacedev

# Run the setup script
cd ../azure-orbital-space-sdk-setup
bash ./.vscode/copy_to_spacedev.sh
```

### Option 2: Create a Local Development Version File

For quick local builds without full setup:

```bash
# Create the config directory
sudo mkdir -p /spacefx-dev/config

# Create the version file
echo "0.11.0" | sudo tee /spacefx-dev/config/spacefx_version

# Link to /var/spacedev
sudo ln -s /var/spacedev /spacefx-dev
```

## Step 5: Using Devcontainers (Optional)

The repository includes a `.devcontainer/devcontainer.json` that automatically sets up the environment:

```json
"features": {
    "ghcr.io/microsoft/azure-orbital-space-sdk/spacefx-dev:0.11.0": {
        "app_name": "spacesdk-client",
        "app_type": "spacesdk-client",
        "dev_language": "python"
    }
}
```

To use devcontainers:

```bash
# Install devcontainer CLI
sudo npm install -g @devcontainers/cli

# Build and start the devcontainer
devcontainer up --workspace-folder ${PWD}
```

The devcontainer feature automatically:
- Installs all dependencies
- Sets up /var/spacedev
- Configures k3s for testing
- Mounts your workspace

## Troubleshooting

### Issue: "Could not find a part of the path '/spacefx-dev/config/spacefx_version'"

**Solution**: Run the setup script from `azure-orbital-space-sdk-setup`:
```bash
cd ../azure-orbital-space-sdk-setup
bash ./.vscode/copy_to_spacedev.sh
```

### Issue: "Protobuf files not found"

**Solution**: Verify protos are installed:
```bash
ls -la /var/spacedev/protos/spacefx/protos/
```

If missing, re-run the setup script.

### Issue: Permission Denied on /var/spacedev

**Solution**: Fix ownership:
```bash
sudo chown -R $USER:$USER /var/spacedev
```

### Issue: GitHub Actions Still Failing

The workflows reference shared actions from `microsoft/azure-orbital-space-sdk-github-actions`.
Check that repository in your parent directory:
```bash
cd ../azure-orbital-space-sdk-github-actions
git pull origin main
```

## Related Repositories

Your workspace has all the necessary repositories:
- `azure-orbital-space-sdk-setup` - Setup scripts and configurations ⭐ **Start here**
- `azure-orbital-space-sdk-client` - This repository (client libraries)
- `azure-orbital-space-sdk-core` - Core SDK
- `azure-orbital-space-sdk-github-actions` - Shared CI/CD workflows
- `azure-orbital-space-sdk-hostsvc-*` - Host services (sensor, position, link, logging)

## Next Steps

1. ✅ Run the setup script: `cd ../azure-orbital-space-sdk-setup && bash ./.vscode/copy_to_spacedev.sh`
2. ⚠️ Verify setup: `cat /var/spacedev/config/spacefx_version`
3. ⚠️ Try building: `dotnet build spacesdk-client.sln`
4. ⚠️ Run tests: `pytest test/unit/`
5. ⚠️ Check GitHub Actions configuration

## Additional Resources

- Main SDK Documentation: `../azure-orbital-space-sdk/docs/`
- Setup Repository: `../azure-orbital-space-sdk-setup/README.md`
- Getting Started Guide: Check `azure-orbital-space-sdk` repo for `docs/getting-started.md`
