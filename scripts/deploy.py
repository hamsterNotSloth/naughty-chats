#!/usr/bin/env python3
"""Idempotent deployment/update script for Naughty Chats (Container Apps on Azure).

(Enhanced) Features:
 - Structured log lines with phases
 - Verification phase (default) ensures new images are active & healthy before success message
 - Optional retries/polling for revision readiness
 - Safe dry-run mode still skips verification logic
 - Explicit non-zero exit on verification failure

Quick Start (most common full deployment):
        python scripts/deploy.py \
            --env dev --region eastus \
            --resource-group rg-nchat-dev --acr acrnchatdev \
            --api-app api-nchat-dev --web-app web-nchat-dev \
            --audience api://<API_APP_ID> \
            --b2c-policy B2C_1_SIGNUPSIGNIN \
            --b2c-domain naughtychats.onmicrosoft.com \
            --spa-client-id <SPA_APP_ID> \
            --api-scope api://<API_APP_ID>/User.Impersonation \
            --tenant-name naughtychats \
            --user-flow B2C_1_SIGNUPSIGNIN

Pass --no-verify to skip post-deployment checks (not recommended).
"""
# Deployment command executed by assistant:
# python3 scripts/deploy.py --env dev --region eastus --resource-group rg-nchat-dev --acr acrnchatdev \
#   --api-app api-nchat-dev --web-app web-nchat-dev --tag 398a265-20250919073849 \
#   --audience api://2b3282d9-d672-4c1e-b963-0d3235cb0f31 --b2c-policy B2C_1_SIGNUPSIGNIN \
#   --b2c-domain naughtychats.onmicrosoft.com --spa-client-id bf515dbe-ecdb-4382-b1f8-ee8d911d5795 \
#   --api-scope api://2b3282d9-d672-4c1e-b963-0d3235cb0f31/.default --tenant-name naughtychats \
#   --user-flow B2C_1_SIGNUPSIGNIN --skip-build
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# ----------------------------- Logging Helpers ---------------------------------

def log(phase: str, msg: str):
    print(f"[{phase.upper()}] {msg}")

# ----------------------------- Subprocess Helper ---------------------------------

def run(cmd: List[str], *, capture=False, check=True, dry_run=False, env=None):
    printable = ' '.join(cmd)
    if dry_run:
        print(f"[DRY-RUN] {printable}")
        return '' if capture else 0
    if capture:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        if check and result.returncode != 0:
            log('error', f"Command failed: {printable}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            raise SystemExit(result.returncode)
        return result.stdout.strip()
    else:
        rc = subprocess.run(cmd, env=env).returncode
        if check and rc != 0:
            log('error', f"Command failed: {printable}")
            raise SystemExit(rc)
        return rc


def run_json(cmd: List[str], *, dry_run=False) -> Any:
    if dry_run:
        print(f"[DRY-RUN] {' '.join(cmd)}")
        return None
    out = run(cmd, capture=True, dry_run=dry_run)
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        log('warn', f"Failed to parse JSON from command: {' '.join(cmd)}")
        return None

# ----------------------------- Git / Tag Helpers ---------------------------------

def git_short_sha() -> str:
    try:
        return run(["git", "rev-parse", "--short", "HEAD"], capture=True, check=True)
    except Exception:
        return "nogit"


def build_tag(override: Optional[str] = None) -> str:
    if override:
        return override
    sha = git_short_sha()
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f"{sha}-{ts}"

@dataclass
class DeployConfig:
    env: str
    region: str
    resource_group: str
    acr: str
    api_app: str
    web_app: str
    backend_path: Path
    frontend_path: Path
    api_image_name: str
    web_image_name: str
    tag: str
    dry_run: bool = False
    disable_acr_admin: bool = True
    add_localhost_cors: bool = True
    verify: bool = True
    verify_timeout: int = 300  # seconds
    verify_interval: int = 10  # seconds

# ------------------------- Core Deployment Logic -----------------------

def acr_login_server(acr: str) -> str:
    return f"{acr}.azurecr.io" if '.' not in acr else acr


def remote_build(acr: str, image_repo: str, tag: str, context_dir: Path, *, dry_run=False):
    log('build', f"Remote build {image_repo}:{tag}")
    run([
        "az", "acr", "build",
        "-r", acr,
        "-t", f"{image_repo}:{tag}",
        str(context_dir)
    ], dry_run=dry_run)


def disable_acr_admin_if_enabled(acr: str, *, dry_run=False):
    enabled = run(["az", "acr", "show", "-n", acr, "--query", "adminUserEnabled", "-o", "tsv"], capture=True, dry_run=dry_run)
    if enabled == 'true':
        log('security', f"Disabling admin user on ACR {acr}")
        run(["az", "acr", "update", "-n", acr, "--admin-enabled", "false"], dry_run=dry_run)


def get_containerapp_fqdn(name: str, rg: str, *, dry_run=False) -> str:
    fqdn = run(["az", "containerapp", "show", "-n", name, "-g", rg, "--query", "properties.configuration.ingress.fqdn", "-o", "tsv"], capture=True, dry_run=dry_run)
    return fqdn


def update_api_container(cfg: DeployConfig, *, cosmos_endpoint: Optional[str], cosmos_key: Optional[str], b2c_policy: Optional[str], b2c_domain: Optional[str], audience: Optional[str], allowed_origins: List[str]):
    log('update', f"Updating API container app {cfg.api_app}")
    env_pairs = {
        "COSMOS_DATABASE": os.getenv("COSMOS_DATABASE", "nchatsdb"),
        "COSMOS_USERS_CONTAINER": os.getenv("COSMOS_USERS_CONTAINER", "users"),
        "COSMOS_CHARACTERS_CONTAINER": os.getenv("COSMOS_CHARACTERS_CONTAINER", "characters"),
        "COSMOS_AUTO_PROVISION": os.getenv("COSMOS_AUTO_PROVISION", "false"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }
    if audience: env_pairs["ENTRA_API_AUDIENCE"] = audience
    if b2c_policy: env_pairs["ENTRA_B2C_POLICY"] = b2c_policy
    if b2c_domain: env_pairs["ENTRA_B2C_TENANT_PRIMARY_DOMAIN"] = b2c_domain
    if allowed_origins:
        env_pairs["ALLOWED_ORIGINS"] = ','.join(allowed_origins)

    base_cmd = [
        "az", "containerapp", "update",
        "-n", cfg.api_app,
        "-g", cfg.resource_group,
        "--image", f"{acr_login_server(cfg.acr)}/{cfg.api_image_name}:{cfg.tag}",
    ]

    secret_args: List[str] = []
    env_set_args: List[str] = []
    if cosmos_endpoint:
        secret_args.append(f"cosmos-endpoint={cosmos_endpoint}")
        env_pairs["COSMOS_ENDPOINT"] = "secretref:cosmos-endpoint"
    if cosmos_key:
        secret_args.append(f"cosmos-key={cosmos_key}")
        env_pairs["COSMOS_KEY"] = "secretref:cosmos-key"

    if secret_args:
        run(["az", "containerapp", "secret", "set", "-n", cfg.api_app, "-g", cfg.resource_group, "--secrets", *secret_args], dry_run=cfg.dry_run)

    for k, v in env_pairs.items():
        env_set_args.append(f"{k}={v}")

    run(base_cmd + ["--set-env-vars", *env_set_args], dry_run=cfg.dry_run)


def update_web_container(cfg: DeployConfig, *, api_base: str, spa_client_id: str, api_scope: str, tenant_name: str, user_flow: str, azure_client_secret: Optional[str]=None, nextauth_secret: Optional[str]=None):
    log('update', f"Updating WEB container app {cfg.web_app}")
    env_pairs = {
        "NEXT_PUBLIC_API_BASE_URL": api_base,
        "NEXT_PUBLIC_ENTRA_CLIENT_ID": spa_client_id,
        "NEXT_PUBLIC_ENTRA_API_SCOPE": api_scope,
        "NEXT_PUBLIC_B2C_TENANT_NAME": tenant_name,
        "NEXT_PUBLIC_B2C_USER_FLOW": user_flow,
    }
    env_set_args: List[str] = []

    # Secrets for server-side NextAuth route and Azure provider
    secret_args: List[str] = []
    if azure_client_secret:
        secret_args.append(f"azure-ad-client-secret={azure_client_secret}")
        env_pairs["AZURE_AD_CLIENT_SECRET"] = "secretref:azure-ad-client-secret"
    if nextauth_secret:
        secret_args.append(f"nextauth-secret={nextauth_secret}")
        env_pairs["NEXTAUTH_SECRET"] = "secretref:nextauth-secret"

    # Public client id still set as env var (not secret)
    env_pairs["AZURE_AD_CLIENT_ID"] = spa_client_id

    for k, v in env_pairs.items():
        env_set_args.append(f"{k}={v}")

    if secret_args:
        # Ensure secrets set on container app
        run(["az", "containerapp", "secret", "set", "-n", cfg.web_app, "-g", cfg.resource_group, "--secrets", *secret_args], dry_run=cfg.dry_run)

    cmd = [
        "az", "containerapp", "update",
        "-n", cfg.web_app,
        "-g", cfg.resource_group,
        "--image", f"{acr_login_server(cfg.acr)}/{cfg.web_image_name}:{cfg.tag}",
        "--set-env-vars", *env_set_args
    ]
    run(cmd, dry_run=cfg.dry_run)

# ------------------------- Verification ---------------------------------

def fetch_active_revisions(app: str, cfg: DeployConfig) -> List[Dict[str, Any]]:
    data = run_json([
        "az", "containerapp", "revision", "list",
        "-n", app, "-g", cfg.resource_group,
        "-o", "json"
    ], dry_run=cfg.dry_run)
    if not data:
        return []
    active = [r for r in data if r.get('properties', {}).get('active')]
    return active


def revision_uses_tag(revision: Dict[str, Any], tag: str) -> bool:
    try:
        containers = revision['properties']['template']['containers']
        if not containers:
            return False
        image = containers[0]['image']
        return image.endswith(f":{tag}")
    except KeyError:
        return False


def verify_rollout(cfg: DeployConfig):
    if cfg.dry_run:
        log('verify', 'Skipping verification in dry-run mode')
        return
    log('verify', 'Starting verification loop')
    deadline = time.time() + cfg.verify_timeout
    needed = {cfg.api_app: False, cfg.web_app: False}

    while time.time() < deadline and (not all(needed.values())):
        for app in list(needed.keys()):
            if needed[app]:
                continue
            revs = fetch_active_revisions(app, cfg)
            if not revs:
                log('verify', f"No active revisions yet for {app}; waiting...")
                continue
            if any(revision_uses_tag(r, cfg.tag) for r in revs):
                log('verify', f"{app}: active revision with tag {cfg.tag} confirmed")
                needed[app] = True
            else:
                log('verify', f"{app}: active revisions found but not yet using tag {cfg.tag}")
        if not all(needed.values()):
            time.sleep(cfg.verify_interval)

    if not all(needed.values()):
        missing = [k for k, v in needed.items() if not v]
        log('error', f"Verification failed. Apps without new tag: {', '.join(missing)}")
        raise SystemExit(2)

    # Basic health probe: attempt simple GET / for web and /healthz for api (best effort)
    try:
        api_fqdn = get_containerapp_fqdn(cfg.api_app, cfg.resource_group, dry_run=cfg.dry_run)
        web_fqdn = get_containerapp_fqdn(cfg.web_app, cfg.resource_group, dry_run=cfg.dry_run)
        if api_fqdn:
            run(["curl", "-fsS", f"https://{api_fqdn}/healthz"], check=False, dry_run=cfg.dry_run)
        if web_fqdn:
            run(["curl", "-I", "-s", f"https://{web_fqdn}"], check=False, dry_run=cfg.dry_run)
    except Exception as e:
        log('warn', f"Health probe encountered error (non-fatal): {e}")

    log('verify', 'Verification successful')

# ------------------------- Arg Parsing ---------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deploy updated images & env to Azure Container Apps (with verification)")
    p.add_argument('--env', required=True)
    p.add_argument('--region', required=True)
    p.add_argument('--resource-group', required=True)
    p.add_argument('--acr', required=True, help='ACR name (without domain)')
    p.add_argument('--api-app', required=True)
    p.add_argument('--web-app', required=True)
    p.add_argument('--backend-path', default='backend')
    p.add_argument('--frontend-path', default='frontend')
    p.add_argument('--api-image-name', default='api')
    p.add_argument('--web-image-name', default='web')
    p.add_argument('--tag', help='Override image tag (otherwise computed)')
    p.add_argument('--audience', help='ENTRA_API_AUDIENCE value for backend')
    p.add_argument('--b2c-policy', help='B2C user flow policy (e.g. B2C_1_SIGNUPSIGNIN)')
    p.add_argument('--b2c-domain', help='Primary domain e.g. tenant.onmicrosoft.com')
    p.add_argument('--spa-client-id', help='Frontend public client id')
    p.add_argument('--api-scope', help='Frontend API scope value (e.g. api://APP_ID/User.Impersonation or .default)')
    p.add_argument('--tenant-name', help='Short tenant name for derived authority')
    p.add_argument('--user-flow', help='User flow/policy for frontend')
    p.add_argument('--azure-client-secret', help='Azure AD client secret (for server-side NextAuth route)')
    p.add_argument('--nextauth-secret', help='NEXTAUTH_SECRET value for NextAuth JWT encryption')
    p.add_argument('--cosmos-endpoint', help='Cosmos endpoint (if updating secret)')
    p.add_argument('--cosmos-key', help='Cosmos key (if updating secret)')
    p.add_argument('--allowed-origins', help='Comma separated allowed origins list')
    p.add_argument('--skip-build', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--keep-acr-admin', action='store_true', help='Do not disable the ACR admin user')
    p.add_argument('--no-verify', action='store_true', help='Skip post-deployment verification (NOT recommended)')
    p.add_argument('--verify-timeout', type=int, default=300, help='Seconds to wait for new revisions (default 300)')
    p.add_argument('--verify-interval', type=int, default=10, help='Seconds between revision polls (default 10)')
    return p.parse_args()

# ------------------------- Main ---------------------------------

def main():
    args = parse_args()
    tag = build_tag(args.tag)
    cfg = DeployConfig(
        env=args.env,
        region=args.region,
        resource_group=args.resource_group,
        acr=args.acr,
        api_app=args.api_app,
        web_app=args.web_app,
        backend_path=Path(args.backend_path),
        frontend_path=Path(args.frontend_path),
        api_image_name=args.api_image_name,
        web_image_name=args.web_image_name,
        tag=tag,
        dry_run=args.dry_run,
        disable_acr_admin=not args.keep_acr_admin,
        verify=not args.no_verify,
        verify_timeout=args.verify_timeout,
        verify_interval=args.verify_interval,
    )

    log('start', f"Deployment starting (tag={cfg.tag})")

    if not args.skip_build:
        remote_build(cfg.acr, cfg.api_image_name, cfg.tag, cfg.backend_path, dry_run=cfg.dry_run)
        remote_build(cfg.acr, cfg.web_image_name, cfg.tag, cfg.frontend_path, dry_run=cfg.dry_run)
    else:
        log('build', 'Skipping image builds (using existing tag)')

    if cfg.disable_acr_admin:
        disable_acr_admin_if_enabled(cfg.acr, dry_run=cfg.dry_run)

    api_fqdn = get_containerapp_fqdn(cfg.api_app, cfg.resource_group, dry_run=cfg.dry_run)
    web_fqdn = get_containerapp_fqdn(cfg.web_app, cfg.resource_group, dry_run=cfg.dry_run)

    allowed_origins: List[str]
    if args.allowed_origins:
        allowed_origins = [o.strip() for o in args.allowed_origins.split(',') if o.strip()]
    else:
        allowed_origins = [f"https://{web_fqdn}"] if web_fqdn else []
        if cfg.add_localhost_cors:
            allowed_origins.append("http://localhost:3000")

    update_api_container(
        cfg,
        cosmos_endpoint=args.cosmos_endpoint,
        cosmos_key=args.cosmos_key,
        b2c_policy=args.b2c_policy,
        b2c_domain=args.b2c_domain,
        audience=args.audience,
        allowed_origins=allowed_origins,
    )

    if all([args.spa_client_id, args.api_scope, args.tenant_name, args.user_flow]):
        api_base = f"https://{api_fqdn}" if api_fqdn else ''
        update_web_container(
            cfg,
            api_base=api_base,
            spa_client_id=args.spa_client_id,
            api_scope=args.api_scope,
            tenant_name=args.tenant_name,
            user_flow=args.user_flow,
            azure_client_secret=args.azure_client_secret,
            nextauth_secret=args.nextauth_secret,
        )
    else:
        log('warn', 'Skipping web env update (missing one of spa-client-id, api-scope, tenant-name, user-flow)')

    if cfg.verify:
        verify_rollout(cfg)
    else:
        log('verify', 'Verification skipped (user requested)')

    log('success', f"Deployment successful. Tag={cfg.tag}")

if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        if e.code != 0:
            log('fail', f"Deployment failed with exit code {e.code}")
        raise
    except Exception as exc:  # catch-all for unexpected errors
        log('fail', f"Unhandled exception: {exc}")
        sys.exit(99)
