#!/usr/bin/env bash
set -u

failures=0

check() {
  local description="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf 'PASS: %s\n' "$description"
  else
    printf 'FAIL: %s\n' "$description"
    failures=$((failures + 1))
  fi
}

for unit in gitea.service nginx.service act_runner.service; do
  check "$unit is enabled" systemctl is-enabled --quiet "$unit"
  check "$unit is active" systemctl is-active --quiet "$unit"
done

for unit in cf-dyn-origin.timer update-cloudflare-realip.timer; do
  check "$unit is enabled" systemctl is-enabled --quiet "$unit"
  check "$unit is active" systemctl is-active --quiet "$unit"
done

for unit in cf-dyn-origin.service update-cloudflare-realip.service; do
  check "$unit last run succeeded" test "$(systemctl show "$unit" -p Result --value)" = success
done

check "act_runner can traverse /run/podman" sudo -u act_runner test -x /run/podman
check "act_runner can ping the Podman API" sudo -u act_runner curl -fsS --max-time 5 --unix-socket /run/podman/podman.sock http://localhost/_ping
check "Gitea health endpoint responds locally" curl -fsS --max-time 5 http://127.0.0.1:3000/api/healthz
check "Gitea responds through local nginx" curl -kfsS --max-time 5 --resolve git.leadt3ch.com:443:127.0.0.1 https://git.leadt3ch.com/api/healthz

if ((failures > 0)); then
  printf '%d check(s) failed.\n' "$failures"
  exit 1
fi

printf 'All automation core-service checks passed.\n'
