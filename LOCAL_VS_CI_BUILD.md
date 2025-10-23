# Local Development vs CI/CD Build Strategy

## TL;DR - Your Concern is Valid! ✅

**You are 100% correct**: You do NOT need to pollute your local WSL environment with `/var/spacedev` just to build on GitHub Actions!

## How GitHub Actions Works (The Good News!)

Looking at the GitHub Actions workflows, here's what happens:

### GitHub Actions Setup (Automatic)

1. **The `initialize` composite action** automatically:
   - Clones `azure-orbital-space-sdk-setup` to `/var/tmp/`
   - Runs `copy_to_spacedev.sh` to create `/var/spacedev`
   - **This happens on the GitHub runner, NOT your local machine!**

2. **Location**: `composite-actions/get-setup/action.yaml`
   ```yaml
   - name: Clone repo
     shell: bash
     run: |
       mkdir -p /var/tmp
       cd /var/tmp
       git clone ${{ inputs.setup-repo-url }}
       cd azure-orbital-space-sdk-setup
       bash ./.vscode/copy_to_spacedev.sh
   ```

3. **When it runs**: Every time the GitHub Actions workflow runs
4. **Where**: On GitHub's runners (clean Ubuntu VMs)
5. **Impact on your machine**: **ZERO** ✅

## Recommended Approach

### For GitHub Actions Builds (Production)

**Do nothing locally!** The workflows are already configured correctly:

```yaml
# .github/workflows/spacefx-client-build.yaml
uses: microsoft/azure-orbital-space-sdk-github-actions/.github/workflows/client-build.yaml@main
with:
  # ... parameters ...
secrets:
  GIT_HUB_USER_NAME: ${{ secrets.GIT_HUB_USER_NAME }}
  GIT_HUB_USER_TOKEN: ${{ secrets.GIT_HUB_USER_TOKEN }}
  SETUP_REPO_URL: ${{ secrets.SETUP_REPO_URL }}  # ← Points to setup repo
```

**What you need to configure:**

1. **GitHub Secrets** (in your fork's settings):
   - `GIT_HUB_USER_NAME` - Your GitHub username
   - `GIT_HUB_USER_TOKEN` - A GitHub Personal Access Token with `packages:read` permission
   - `SETUP_REPO_URL` - The URL to clone azure-orbital-space-sdk-setup
     - For Microsoft repo: `https://github.com/microsoft/azure-orbital-space-sdk-setup`
     - For your fork: `https://github.com/montge/azure-orbital-space-sdk-setup` (or wherever you forked it)

2. **That's it!** GitHub Actions will handle everything else.

### For Local Development (Optional)

You have **THREE OPTIONS**:

#### Option 1: Don't Build Locally (Recommended for Your Use Case)

**Just use GitHub Actions for all builds!**

Pros:
- ✅ No local environment pollution
- ✅ Consistent with production builds
- ✅ No setup hassle
- ✅ Works on any machine

Cons:
- ❌ Slower feedback loop (wait for CI)
- ❌ Need internet connection
- ❌ Uses GitHub Actions minutes

**When to use**: When you're mainly fixing security issues, updating dependencies, or making small changes that don't need rapid iteration.

#### Option 2: Use Docker/Devcontainer (Best of Both Worlds)

**Use the provided `.devcontainer/` configuration**

```bash
# Install devcontainer CLI
npm install -g @devcontainers/cli

# Build and start devcontainer
devcontainer up --workspace-folder ${PWD}

# The devcontainer automatically:
# - Sets up /var/spacedev INSIDE the container
# - Installs all dependencies
# - Keeps your host machine clean!
```

Pros:
- ✅ No local WSL pollution (isolated in container)
- ✅ Fast local builds
- ✅ Matches CI environment
- ✅ Can commit and test locally

Cons:
- ❌ Requires Docker
- ❌ Initial setup time
- ❌ Uses disk space for container

**When to use**: When you need rapid local iteration and testing.

#### Option 3: Minimal Local Setup (Only if Necessary)

If you **really** need to build locally without Docker:

```bash
# Create a minimal version file for local builds
sudo mkdir -p /spacefx-dev/config
echo "0.11.0" | sudo tee /spacefx-dev/config/spacefx_version

# Link to avoid full /var/spacedev setup
sudo ln -s /spacefx-dev /var/spacedev
```

**However**, this won't work for full builds because you'll still be missing:
- Protobuf files
- Build scripts
- Other dependencies

So you'd still need to run `copy_to_spacedev.sh` eventually.

## What I Recommend for You

Based on your concerns and goals:

### Phase 1: Security Updates & Dependency Management (Now)
**Use GitHub Actions only!**

1. Keep making code changes locally
2. Commit and push to GitHub
3. Let GitHub Actions build and test
4. Monitor the workflows to ensure they pass

**What you've done so far:**
- ✅ Updated .NET packages
- ✅ Updated Python packages
- ✅ Created Dependabot config
- ✅ Fixed workflow references

**Next steps:**
1. Configure GitHub Secrets (if not already done)
2. Push your changes
3. Trigger the workflow and see if it builds

### Phase 2: If You Need Local Development Later
**Use devcontainers** - they're already configured in `.devcontainer/devcontainer.json`

The devcontainer feature automatically:
- Downloads and sets up the SpaceSDK environment
- Creates `/var/spacedev` inside the container
- Keeps your WSL clean!

## The `/var/spacedev` Design Decision

You're right to question this design. Here's why Microsoft chose this approach:

### Why `/var/spacedev`?

1. **Satellite deployment compatibility** - Real satellites use this path
2. **Shared location** - Multiple repos reference same setup
3. **CI/CD consistency** - Same path in dev/test/prod
4. **Historical reasons** - Legacy from earlier versions

### Is it ideal?

**No, especially for WSL development!** Better alternatives would be:
- Environment variables pointing to configurable paths
- Docker volumes
- Workspace-relative paths

But changing this would require updates across the entire ecosystem, which is why they stuck with it.

## Summary

| Approach | Local Pollution | Speed | CI Match | Recommended For |
|----------|----------------|-------|----------|-----------------|
| GitHub Actions Only | ✅ None | ⏱️ Slow | ✅ Perfect | Security updates, small changes |
| Devcontainer | ✅ None (in container) | ⚡ Fast | ✅ Perfect | Active development |
| Local Setup | ❌ High | ⚡ Fast | ⚠️ Depends | Not recommended |

## For Your Current Goal

**Recommendation**: **Use GitHub Actions only!**

You want to:
- Fix security issues ✅
- Update dependencies ✅
- Get it working with GitHub Actions ✅
- Work with your fork on Montge ✅

**None of these require local `/var/spacedev` setup!**

## Next Steps

1. **Configure GitHub Secrets** in your fork's repository settings
2. **Push your current changes** (all the updates we made)
3. **Trigger the GitHub Actions workflow** (manual or via push to main)
4. **Monitor the build** to ensure it works
5. **Iterate** if there are issues

The `/var/spacedev` setup will happen automatically on GitHub's runners, completely isolated from your WSL environment!

## Questions to Answer

Before we proceed, please confirm:

1. **Do you have access to configure GitHub Secrets** in your fork?
2. **What's the URL of your fork** on Montge? (so we can update references if needed)
3. **Do you plan to do active development** or just security/dependency updates?

Based on your answers, I can help you configure the exact setup you need!
