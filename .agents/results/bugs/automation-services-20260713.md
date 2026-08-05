# Automation core services unavailable after reboot

Date: 2026-07-13
Host: `automation.leadt3ch.com`
Status: Runtime incident resolved

## Symptom

- `https://git.leadt3ch.com` returned Cloudflare 522/523 responses.
- Gitea and nginx were inactive after the host reboot.
- The Gitea Actions runner restarted every five seconds.
- Dynamic DNS and Cloudflare Real-IP updates no longer ran.

## Root Cause

The services `gitea.service` and `nginx.service` and the timers
`cf-dyn-origin.timer` and `update-cloudflare-realip.timer` had been running
before shutdown but were disabled. They therefore did not start again after
the reboot.

The Actions runner belonged to the `podman` group and the Podman socket was
group-readable, but `/usr/lib/tmpfiles.d/podman.conf` recreated the parent
directory `/run/podman` as `0700 root:root`. The runner could not traverse the
directory and accumulated 8,436 restart attempts.

The disabled Dynamic DNS timer also left `automation.leadt3ch.com` pointing to
the previous public IPv4 and IPv6 addresses. Cloudflare could not reach the
origin until the updater ran.

## Fix Applied

- Enabled and started `gitea.service` and `nginx.service`.
- Enabled and started `cf-dyn-origin.timer` and
  `update-cloudflare-realip.timer`.
- Ran both updater services successfully.
- Added `/etc/tmpfiles.d/podman.conf`, overriding `/run/podman` to
  `0750 root:podman` while preserving the vendor tmpfiles entries.
- Applied the corrected runtime ownership and mode and restarted
  `act_runner.service`.
- Dynamic DNS updated the A and AAAA records to the current public addresses.

No reboot was performed.

## Regression Test

Test: `.agents/results/bugs/check-automation-core-services.sh`

Before the fix, 13 checks failed. After the fix, all checks passed, including:

- enabled and active state for Gitea, nginx, the runner, and both timers;
- successful last run for both updater services;
- Podman API access as the `act_runner` user;
- direct Gitea health response;
- Gitea health response through local nginx.

Additional verification:

- `systemctl is-system-running`: `running`
- failed units: zero
- public IPv4 health endpoint: HTTP 200
- public IPv6 health endpoint: HTTP 200
- `fj repo view -R leadt3ch/automation-infra`: successful
- Gitea MCP repository listing: successful

## Similar Patterns

The research-only scan of `leadt3ch/automation-infra` found no additional
currently failed versioned unit. Static timer-triggered services being
`inactive/dead` after successful completion is normal.

Two durable repository gaps remain:

1. `deploy/deploy.sh` installs systemd units and runs `daemon-reload`, but does
   not reconcile enablement for Gitea, nginx, or the timers.
2. Runner provisioning is Docker-only and rewrites `docker_host` to
   `/var/run/docker.sock`, while the live server currently uses Podman. The
   Podman tmpfiles and socket configuration is not represented in Git.

These gaps did not prevent runtime recovery, but a future deploy or rebuild can
reintroduce the incident. They require a separate source-controlled change in
`automation-infra` after selecting Docker or Podman as the authoritative
runner backend.
