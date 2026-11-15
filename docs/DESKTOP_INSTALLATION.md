# Desktop builds and installation status

The **Build desktop installers** GitHub Actions workflow builds a Windows x64 NSIS installer, separate Apple Silicon and Intel Mac DMG/ZIP downloads, and Linux x64 AppImage/DEB packages. End users do not install Node or Python. Build artifacts are available to signed-in repository users for 14 days; they are not permanent public releases.

Windows: run the installer and choose the per-user installation folder. Mac: open the DMG and copy the application into Applications. Linux: install the DEB using the distribution package manager, or make the AppImage executable and run it. Linux architectures other than x64 are not included yet.

These are unsigned development builds, not production-trusted installers. Do not disable operating-system security or bypass a block to install them. Public distribution requires Windows signing and Apple Developer signing/notarization, plus native installation testing. No signing credentials have been configured. Automatic application updates are not implemented.

## Implemented desktop workflow

1. Install and open the app.
2. Read the first-run guide.
3. Browse the bundled source library and timeline.
4. Inspect named evidence requirements.
5. Choose a requested PDF or CSV using the operating-system file picker.
6. Validate and store it in the application's private local quarantine directory.
7. Report that the file remains local, unscanned and unapproved.

The sandboxed renderer has no Node access. Its preload exposes only version lookup and bounded request-specific file import. Main-process handlers validate the caller and request against bundled configuration. Uploaded filenames never become storage paths. User documents are not executed, rendered or sent to an AI model. API credentials are never bundled.

## Remaining end-to-end work

This build does **not** yet submit quarantined documents to Cloudflare, authenticate end users, connect desktop screens to live R2 readiness, run malware scanning, approve evidence, train a validated forecast model, or implement signed automatic updates. These are required before describing the entire product as complete. The server-side operator CLI, R2 collector and evidence readiness gate already exist separately.

Mac and Windows smoke tests start the real Electron app, load the bundled JSON, and verify the constrained preload bridge. Linux packaging and input tests run in CI; GUI installation testing on actual target devices remains necessary.
