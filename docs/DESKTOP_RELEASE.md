# Desktop installation and release

Institutional Signals is an Electron application. The desktop frontend is bundled locally; the optional evidence workspace uses an explicitly configured HTTPS service. Do not claim that installing the desktop app activates collection, ingestion, or forecasting.

## Build installers

GitHub: **Actions → Desktop installers → Run workflow**, select `main`. The workflow runs validation and packaging on native Windows, macOS, and Linux hosted runners. Successful runs produce separate **Artifacts** called `institutional-signals-windows`, `institutional-signals-macos`, and `institutional-signals-linux`. Download and extract each ZIP to get its installers. Failed jobs do not upload a valid installer.

To create a public release, create and push a version tag of the form `v0.2.0` (use a new version for subsequent releases). The workflow assembles a **draft GitHub Release** from the platform artifacts. Review the assets before publishing it.

## End users

- **Windows:** download the NSIS `.exe` installer, run it and follow the installation prompts.
- **macOS:** download the `.dmg`, open it and drag the application to Applications. An unsigned/unnotarized build may be blocked by Gatekeeper; production releases require Developer ID signing and Apple notarization.
- **Linux:** download the `.AppImage`, mark it executable (`chmod +x <filename>.AppImage`) and launch it, or install the `.deb` using the distribution's package manager on supported Debian/Ubuntu systems.

These builds are **not claimed to be tested on physical end-user computers** merely because automated packaging succeeds. Release acceptance requires an install / launch / update / uninstall test on real supported operating systems, a security review, signing and notarization strategy, verified architecture coverage, and a reproducible dependency lockfile.

## Local development

```bash
python scripts/build_data.py --check
python -m unittest discover -s tests -v
npm install
npm run build
npm run test:desktop
npm run desktop:package
```

The desktop release workflow also runs the provenance and Cloudflare Worker tests. Do not ship a build if those fail.

## Remaining production blockers

1. Commit a generated `package-lock.json`, then replace `npm install` with `npm ci` in CI for deterministic dependency resolution.
2. Confirm the three native CI builds, smoke-test the packaged app on each OS, and provide support/install troubleshooting.
3. Add trusted signing for Windows, Developer ID signing and notarization for macOS.
4. Decide release/update versioning and authenticated auto-update strategy.
5. Connect evidence review, source health, extraction and forecasts to the UI; installers alone do not deliver the full product.
