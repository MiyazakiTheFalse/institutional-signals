# Desktop builds and installation status

The **Build desktop installers** GitHub Actions workflow builds a Windows x64 NSIS installer, separate Apple Silicon and Intel Mac DMG/ZIP downloads, and Linux x64 AppImage/DEB packages. End users do not install Node or Python. Build artifacts are available to signed-in repository users for 14 days; they are not permanent public releases.

Windows: run the installer and choose the per-user installation folder. Mac: open the DMG and copy the application into Applications. Linux: install the DEB using the distribution package manager, or make the AppImage executable and run it. Linux architectures other than x64 are not included yet.

These are unsigned development builds, not production-trusted installers. Do not disable operating-system security or bypass a block to install them. Public distribution requires Windows signing and Apple Developer signing/notarization, plus native installation testing. No signing credentials have been configured. Automatic application updates are not implemented.

## Implemented desktop workflow

1. Install and open the app.
2. Read the first-run guide.
3. Browse the bundled source library and timeline.
4. Inspect named evidence requirements.
5. Provide the original publisher URL and publication date, then choose the requested PDF or CSV.
6. Validate and store it in the application's private local quarantine directory.
7. Connect an operator-provisioned workspace using an individual invitation key, then submit the document to cloud quarantine.
8. Inspect collector health, live missing-evidence requests, submission receipts and review history. Reviewer-role users can append change requests or rejections.
9. Explore the institutional graph by entity and historical cutoff; inspect provenance and briefing summaries. Empty graph relationships are explicitly marked as unreviewed/missing.

The sandboxed renderer has no Node access. Its preload exposes a narrow set of import, workspace and review operations; main-process handlers validate their caller. The server validates all uploads and reviewer permissions independently. Uploaded filenames never become storage paths. User documents are not executed, rendered or sent to an AI model. R2 credentials are never bundled. Invitation keys use operating-system encrypted storage where available and otherwise remain in memory only.

## Remaining end-to-end work

The desktop/cloud integration is implemented but needs a deployed and provisioned Worker to operate. The ClamAV scan and trusted operator promotion commands need a real uploaded-document integration test. No trained production forecast model, signed automatic updater or completed clean-machine installation certification is claimed. See PRODUCT_ACCEPTANCE.md for the current implementation/deployment distinction.

Mac and Windows smoke tests start the real Electron app, load the bundled JSON, and verify the constrained preload bridge. Linux packaging and input tests run in CI; GUI installation testing on actual target devices remains necessary.
