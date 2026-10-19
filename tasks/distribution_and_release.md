# Distribution and Release Roadmap

Recorded on 2026-10-18. This roadmap tracks the next release, Homebrew,
Microsoft Store distribution, and an installation website. It records planned
work, not the availability or approval of those distribution channels.

## Confirmed Decisions

| ID | Decision | Status |
| --- | --- | --- |
| DIST-001 | Offer a Mac DMG, optional Homebrew installation, an unsigned Windows installer, and a Microsoft Store version. | `RECORDED` |
| DIST-002 | Keep the Mac app unsigned for public distribution for now: no Apple Developer ID signing or notarization. Retain the build's existing technical ad-hoc signature and accurate first-launch instructions. | `RECORDED` |
| DIST-003 | Keep the project free, open source, and independently published by its US-based maintainer. No church or other organization account is required. | `RECORDED` |

Developer ID signing and notarization are deferred until the maintainer chooses
to revisit them. Microsoft Store signing applies to the Store-distributed MSIX;
the separate Windows EXE installer remains unsigned under this roadmap.

## Baseline and Dependencies

- The requested release baseline is `master` at
  `c793d0f9a4e7598d8a93b1b49e36ad1298f8abe2`. The project version and existing tag
  are `0.1.0` / `v0.1.0`. Select a new version; do not replace published assets
  or reuse the published tag. Release preparation may add version/documentation
  changes; unrelated feature work should not silently change this baseline.
- macOS currently produces an ad-hoc-signed Apple Silicon DMG for macOS 14+.
  Homebrew must not be described as removing its first-launch restrictions.
- Windows currently produces an unsigned Inno Setup x64 installer containing a
  PyInstaller application and bundled FFmpeg tools. MSIX packaging does not yet
  exist.
- The maintainer has created the `Trivia Countdown` MSIX/PWA product and its
  package identity in Partner Center, created and associated the
  `TriviaCountdown.onmicrosoft.com` Entra tenant, registered a Store automation
  application, and granted it the `Manager (Windows)` role. The four expected
  GitHub Actions secrets are configured. Account verification/submission access
  and authenticated CLI read access still need verification. The first Store
  submission must be made through Partner Center; the CLI is for updates after
  the app is published.
- [Windows preview qualification](windows_preview_qualification.md) still says
  **NOT APPROVED FOR PUBLICATION**. Separate-system testing, DPI/icon/playback,
  version-changing upgrade, and human source/license approvals remain pending.
  [The Windows tracker](port_to_windows.md) remains the source of detailed
  Windows evidence; this roadmap does not close or duplicate those approvals.
- Builds and draft releases follow [Building and Releasing](../docs/06-building-and-releasing.md).
  Each distributed media build needs its matching corresponding-source archive,
  notices, and build instructions. The repository's automatic source ZIP is not
  a substitute for the FFmpeg source archive.

## Task Statuses

- `READY`: requirements are clear and work can start.
- `PLANNED`: identified work with unfinished dependencies or decisions.
- `BLOCKED`: an explicit unresolved blocker prevents completion.
- `IN_PROGRESS`: actively being worked on.
- `IN_REVIEW`: implementation or submission exists and awaits verification.
- `VERIFIED`: completion criteria passed, with evidence recorded.

All implementation checkboxes start unchecked. When completing a task, update
its status and record the commit, build/submission URL, test results, or public
URL that establishes completion. A successful build alone is not release or
Store approval. `RECORDED` above means a product decision, not tested software.

## 1. Release From the Current Master Baseline

### REL-001 — Select the release version and channel

- [ ] **Status: READY. Dependencies: none.**
- Choose the next version and whether this release is a preview/prerelease or
  stable. Reconcile that choice with the current preview-only release guidance.
- Record the baseline and exact release commit. Explain any changes beyond
  version metadata, documentation, and necessary qualification fixes.
- **Done when:** version, release designation, scope, and candidate commit are
  recorded; `v0.1.0` remains unchanged.

### REL-002 — Complete the outstanding publication qualification

- [ ] **Status: BLOCKED. Dependencies: REL-001; existing Windows qualification blockers.**
- Review and finish the applicable checks in
  [Windows preview qualification](windows_preview_qualification.md), including
  securing a separate live Windows x64 machine and retaining human approvals.
- Re-run applicable Windows and macOS checks for the actual release candidate;
  earlier automation for a different commit is supporting evidence only.
- **Done when:** the linked tracker/checklist records the candidate's required
  results and approvals, with no unresolved publication blocker.

### REL-003 — Prepare version metadata, release notes, and documentation

- [ ] **Status: PLANNED. Dependencies: REL-001.**
- Update `pyproject.toml`, regenerate `uv.lock`, and describe changes since
  `v0.1.0`, including the Windows build and paginated question browser.
- Reconcile README, every file in `docs/`, and notices against actual platform
  support, unsigned-installation behavior, and the selected release channel.
- **Done when:** version/lockfile agree and reviewed notes and instructions
  describe the candidate without advertising unfinished channels.

### REL-004 — Build and verify the release artifacts

- [ ] **Status: PLANNED. Dependencies: REL-003.**
- Build Mac and Windows artifacts using the existing workflows; retain test
  reports, platform-specific corresponding sources, checksums, and provenance.
- Verify both app packages and source archives; qualify the exact artifacts
  intended for publication under REL-002.
- **Done when:** candidate artifacts are identified by commit, workflow run,
  filenames, and hashes, and their required checks pass.

### REL-005 — Tag and publish the new release

- [ ] **Status: PLANNED. Dependencies: REL-002, REL-003, REL-004.**
- Create a new tag matching the project version. Inspect the workflows' draft
  prerelease, repeat required verification for the tagged artifacts, and obtain
  maintainer publication approval. Explicitly set the agreed release channel.
- Include both platform downloads, corresponding-source archives, checksums,
  and accurate unsigned-build caveats. Never overwrite a published asset.
- **Done when:** the new release is public with the approved artifacts and
  release notes; the previous release remains intact.

### REL-006 — Verify the published download experience

- [ ] **Status: PLANNED. Dependencies: REL-005.**
- Download through a browser using public release links and follow the Mac and
  Windows installation, launch, sample-input, and render instructions.
- **Done when:** public URLs, downloaded hashes, platform results, and any
  observed security prompts are recorded for the published artifacts.

## 2. Homebrew Installation for macOS

### BREW-001 — Confirm the unsigned app's Homebrew distribution approach

- [ ] **Status: READY. Dependencies: none.**
- Investigate a project-maintained tap/cask for the existing DMG and verify
  current Homebrew behavior and policy on a supported Mac.
- Official `homebrew/cask` has Gatekeeper acceptance requirements; upstream
  inclusion is not assumed. A custom tap is the proposed initial route, subject
  to verification. Do not remove quarantine or disable Gatekeeper to make the
  installation appear warning-free.
- **Done when:** a workable approach, tap/token naming, supported versions, and
  observed first-launch behavior are documented. If the unsigned binary path
  is not viable, record the blocker and a maintainer decision before proceeding.

### BREW-002 — Create the tap and versioned cask

- [ ] **Status: PLANNED. Dependencies: BREW-001, REL-006.**
- Create a public maintainer-owned tap repository and cask with an immutable
  release URL, SHA-256, application bundle, macOS/architecture requirements,
  homepage, and accurate caveats. Provide sample-CSV access and source links.
- **Done when:** the tap is public and a documented install command resolves
  to the approved release without installing separate Python or FFmpeg tools.

### BREW-003 — Verify install, launch, upgrade, and uninstall

- [ ] **Status: PLANNED. Dependencies: BREW-002.**
- Test download validation, installation, documented first launch, preview and
  render, version-changing upgrade, and uninstall without deleting user files.
- **Done when:** commands and results are recorded on a supported Apple Silicon
  Mac, including any trust prompts and Gatekeeper interaction.

### BREW-004 — Document and maintain the Homebrew channel

- [ ] **Status: PLANNED. Dependencies: BREW-003.**
- Add verified installation/update/uninstall commands to the tap README and
  project installation guide. Document how releases update the cask version,
  URL, and checksum, with testing before publication.
- **Done when:** instructions match the tested tap and the update procedure is
  repeatable. Homebrew is described as optional for DMG users.

## 3. Microsoft Partner Center and Store Distribution

### STORE-001 — Confirm account access and reserve the product

- [ ] **Status: IN_REVIEW. Dependencies: none.**
- Confirm the independent developer account can submit Windows apps. Reserve
  the product name and record Store product ID, package identity name,
  publisher identity, and publisher display name from Partner Center.
- **Done when:** the product exists and its exact non-secret identity values
  are available for packaging; account verification and submission access are
  confirmed. Product creation and identity capture are complete; account access
  confirmation remains open. Do not put credentials in the repository.

### STORE-002 — Add MSIX packaging for the existing desktop application

- [ ] **Status: PLANNED. Dependencies: STORE-001.**
- Package the existing PyInstaller output with a manifest, Store visual assets,
  x64/Windows requirements, valid version mapping, and necessary desktop
  capabilities. Include bundled tools, fonts, notices, and sample CSV access.
- Account for protected installation files and writable user/temp/output paths.
  Retain the separate unsigned Inno Setup distribution.
- **Done when:** a repeatable Windows command produces a Partner Center-ready
  MSIX with the correct identity, without purchasing a public signing certificate
  for Store submission. Record the separate local-test installation method.

### STORE-003 — Qualify the installed MSIX

- [ ] **Status: PLANNED. Dependencies: STORE-002.**
- Test installed startup without system Python/FFmpeg, file dialogs and paths,
  previews, audio/silent renders, cancellation, overwrite/locked-output behavior,
  sample access, DPI/icons, version-changing upgrade, and uninstall.
- Run applicable Windows App Certification Kit checks. Verify packaged FFmpeg
  subprocesses and preservation of user inputs/outputs through updates/removal.
- **Done when:** automated and live-system MSIX results are recorded and
  package-specific failures are resolved; EXE results alone are insufficient.

### STORE-004 — Prepare the Store listing and distribution materials

- [ ] **Status: PLANNED. Dependencies: STORE-001.**
- Prepare the description, screenshots, logos, category, free pricing/markets,
  age-rating answers, privacy/support URLs, and capability explanations needed
  for certification. Explain local processing and user-provided video/CSV inputs.
- Provide durable public access to matching FFmpeg sources/build instructions
  and licenses for every Store version, including after a later update.
- **Done when:** required listing fields and public materials are reviewed,
  accessible, and consistent with the package and its actual data behavior.

### STORE-005 — Build in GitHub Actions and make the first submission

- [ ] **Status: PLANNED. Dependencies: REL-002, STORE-003, STORE-004.**
- Add reproducible MSIX artifact generation and validation to Windows CI.
  Download the verified package and upload the first submission manually in
  Partner Center; check identity and validation results before certification.
- **Done when:** a submission references the exact tested CI package and its
  corresponding-source materials, with build URL, hash, and submission ID recorded.

### STORE-006 — Complete certification and verify Store installation

- [ ] **Status: PLANNED. Dependencies: STORE-005.**
- Resolve certification feedback, publish the free listing, and install from
  the actual Store. Recheck launch, preview, render, sample access, and updates
  when a newer Store version is available.
- **Done when:** certification and public listing are confirmed, a Store-installed
  render passes, and the public product URL and tested version are recorded.

### STORE-007 — Verify GitHub Actions authentication and product read access

- [ ] **Status: IN_REVIEW. Dependencies: STORE-001.**
- Configure the Microsoft Store CLI in a manually triggered GitHub Actions
  workflow using the Entra tenant/client IDs, client secret, and Partner Center
  Seller ID stored as repository secrets. The workflow checks secret presence,
  authenticates, and makes a read-only request for the reserved Store product.
- Do not print secrets or product response data. A reserved, unpublished product
  may not be accessible through CLI APIs; record authentication and product-access
  outcomes separately and interpret any pre-publication limitation accordingly.
- **Done when:** the workflow run proves authentication and read access to the
  intended product, or records a documented Microsoft first-publication limit;
  no secrets appear in source or logs.

### STORE-008 — Automate subsequent Partner Center submissions

- [ ] **Status: PLANNED. Dependencies: STORE-006, STORE-007.**
- Use the supported Microsoft Store CLI/GitHub Actions authentication to submit
  tested, versioned MSIX updates, with an explicit maintainer-controlled
  submission step. Document credential renewal and required account configuration.
  Track certification separately from upload success.
- **Done when:** a later release is submitted through Actions and its Store
  update is verified; no secrets appear in source or logs.

## 4. Installation Website

### WEB-001 — Build a static site and deploy it with GitHub Pages

- [ ] **Status: READY. Dependencies: none.**
- Select a source directory that does not conflict with the existing `docs/`
  guides. Use a small static site and a repeatable Pages deployment; the free
  GitHub Pages address is sufficient initially.
- **Done when:** the public HTTPS site deploys from the repository and works at
  its actual project-site base path. A custom domain is optional later work.

### WEB-002 — Add product information and getting-started resources

- [ ] **Status: PLANNED. Dependencies: WEB-001.**
- Add the demo, short explanation, platform requirements, sample CSV, own-video
  requirement, local-processing privacy explanation, documentation, support,
  releases, and source/license links.
- **Done when:** a visitor can understand the app, obtain sample questions, and
  find the requirements and help without navigating the source repository.

### WEB-003 — Add all four installation paths

- [ ] **Status: PLANNED. Dependencies: WEB-002; channel tasks listed below.**
- Mac DMG: direct versioned download, drag-to-Applications/sample instructions,
  and accurate unsigned first-launch guidance; requires REL-006.
- Windows EXE: direct installer download, requirements, installation steps,
  checksum/source access, and accurate SmartScreen guidance; requires REL-006.
- Homebrew: tested tap/install/update commands and first-launch caveats;
  requires BREW-004.
- Microsoft Store: verified product link, requirements, and installation steps;
  requires STORE-006. Prefer this path for ordinary Windows users once available.
- **Done when:** each available path is usable from the website and links to the
  verified artifact/product/commands. Until then, show an honest planned or
  unavailable state instead of a working-looking placeholder button.

### WEB-004 — Keep availability and versions accurate

- [ ] **Status: PLANNED. Dependencies: WEB-002, REL-001.**
- Define how public release assets, tap versions, and Store availability are
  represented. Do not assume GitHub's `releases/latest` resolves a prerelease or
  that both platforms publish simultaneously.
- **Done when:** links target the intended public version, unpublished channels
  stay unavailable, and website updates follow verified channel publication.

### WEB-005 — Verify website instructions and documentation consistency

- [ ] **Status: PLANNED. Dependencies: WEB-003, WEB-004.**
- Follow all four paths on their supported systems. Check downloads, checksums,
  commands, Store links, mobile layout, keyboard navigation, image descriptions,
  and legible requirements/security information.
- Compare README, every file under `docs/`, tap guidance, and website text;
  update conflicting commands, statuses, defaults, and platform claims together.
- **Done when:** installation evidence and link/accessibility checks are recorded
  and the documentation agrees with all publicly available channels.

### WEB-006 — Document ongoing release and website maintenance

- [ ] **Status: PLANNED. Dependencies: WEB-005, BREW-004, STORE-008.**
- Document the sequence for GitHub artifacts/sources, cask changes, Store
  submission/certification, and website links, including partial publication
  failures and retaining older versions' required source materials.
- **Done when:** a maintainer can follow one documented release/update procedure
  without advertising a channel before it is ready.

## Suggested Execution Order

1. Start REL-001, BREW-001, and STORE-001; build the website skeleton in parallel
   if desired. Source/license and separate-system qualification remain explicit
   release dependencies.
2. Prepare candidate metadata and builds (REL-003/REL-004), finish qualification
   (REL-002), then publish and verify the unsigned downloads (REL-005/REL-006).
3. Complete Homebrew and MSIX packaging/testing. These tracks can proceed
   independently once their prerequisites are available.
4. Publish each installation path on the website only after its verification.
5. Configure and verify the Store automation identity and GitHub Actions read
   access early (STORE-007); defer Store update automation until after the app's
   first manual Partner Center publication (STORE-008).
6. Finish the shared release and website maintenance procedure.

## References

- [Installation guide](../docs/01-installation.md)
- [Building and releasing](../docs/06-building-and-releasing.md)
- [Windows task tracker](port_to_windows.md)
- [Windows preview qualification](windows_preview_qualification.md)
- [Homebrew acceptable casks](https://docs.brew.sh/Acceptable-Casks)
- [Creating and maintaining a Homebrew tap](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Microsoft Store MSIX package requirements](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements)
- [Microsoft Store EXE/MSI requirements](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/app-package-requirements)
- [Microsoft Store updates with GitHub Actions](https://learn.microsoft.com/en-us/windows/apps/publish/msstore-dev-cli/github-actions)
- [Microsoft Store Developer CLI (MSIX)](https://learn.microsoft.com/en-us/windows/apps/publish/msstore-dev-cli/overview)
