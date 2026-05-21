# gVisor Configuration for LLM Sandbox

gVisor provides kernel-intercept sandboxing for container isolation, as required by ARCH-06.

## Installation

### Linux

```bash
# Download runsc binary
curl -O https://gvisor.dev/releases/runsc

# Make executable
chmod +x runsc

# Move to system PATH
sudo mv runsc /usr/local/bin/

# Install as Docker runtime
sudo runsc install
```

### Configure Docker Daemon

Edit `/etc/docker/daemon.json`:

```json
{
  "runtimes": {
    "runsc": {
      "path": "/usr/local/bin/runsc",
      "runtimeArgs": ["--net-raw", "--allow-packet-socket-write", "--platform=systrap"]
    }
  }
}
```

Restart Docker: `sudo systemctl restart docker`

## Windows/macOS Fallback

gVisor requires Linux kernel features and is not available on Windows or macOS natively.

**Option 1: Docker Desktop with WSL2 (Windows)**
- Install Docker Desktop with WSL2 backend
- Use Linux containers (default)
- gVisor will work inside the WSL2 VM

**Option 2: Native Docker Runtime (Reduced Isolation)**
If gVisor is unavailable, use the standard Docker runtime by removing the runtime override:

```yaml
# docker-compose.yml
llm-sandbox:
  # Remove runtime: runsc to use default runc
  runtime: runc  # Provides basic isolation only
```

**Note:** ARCH-06 (gVisor) requires Linux for full kernel-intercept isolation. The runc fallback provides basic namespace isolation but does not implement the same security boundaries as gVisor.

## Verification

Verify gVisor is available:

```bash
docker run --rm --runtime=runsc hello-world
```

If you see "runtime runsc not found", gVisor is not installed correctly.