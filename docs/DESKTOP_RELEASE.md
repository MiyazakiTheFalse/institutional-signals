# Desktop installation and release

Institutional Signals is an Electron application. The desktop frontend is bundled locally; the optional evidence workspace uses an explicitly configured HTTPS service. Do not claim that installing the desktop app activates collection, ingestion, or forecasting.

## Build installers

GitHub: **Actions → Build desktop installers → Run workflow**, select `main`. The canonical workflow is `.github/workflows/desktop.yml`. A `v*` tag also triggers builds. Ordinary pushes and pull requests run validation only; native installers are generated deliberately to limit artifact storage. The workflow tests, builds and packages on native Windows, macOS, and Linux standard runners. Successful runs produce **Artifacts** named `institutional-signals-windows-x64`, `institutional-signals-mac-universal-downloads` (separate Intel/Apple Silicon artifacts), and `institutional-signals-linux-x64`. Download and extract each ZIP to get the installers. All native jobs use the committed `package-lock.json` with `npm ci`, so dependency resolution is consistent across runs. Failed jobs must not be treated as accepted releases.

Version tags of the form `v0.2.0` also trigger packaging. **This workflow does not publish a GitHub Release automatically.** Review and test the build artifacts before manually creating a release. Installer artifacts are retained for one day to minimise billable storage; save approved binaries to a deliberately managed release destination.

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

The canonical desktop workflow runs the provenance and Cloudflare Worker tests. Do not ship a build if those fail.

## Remaining production blockers

1. Verify the committed `package-lock.json` stays in sync with each deliberate package update; require `npm ci` in every release build.
2. Confirm the three native CI builds, smoke-test the packaged app on each OS, and provide support/install troubleshooting.
3. Add trusted signing for Windows, Developer ID signing and notarization for macOS.
4. Decide release/update versioning and authenticated auto-update strategy.
5. Connect evidence review, source health, extraction and forecasts to the UI; installers alone do not deliver the full product.
