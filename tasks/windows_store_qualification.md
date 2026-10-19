# Microsoft Store MSIX Qualification

**Status: NOT APPROVED FOR SUBMISSION OR PUBLICATION.** Packaging implementation
is present; its first Windows build, installed-package checks, WACK, source/license
approval, and live-system qualification are pending. App **0.1.1** / Store
package **1.0.1.0** is the selected candidate pair. Do not check an unobserved result.

## Candidate identity and build

- Tester/date and Windows edition/build/native x64 architecture:
- App version, four-part Store version, commit and CI run URL:
- SDK/MakeAppx version/path, WACK version:
- Original unsigned MSIX filename/SHA-256:
- Source archive filename/SHA-256 and durable public source URL:
- Test-signed copy hash and temporary certificate thumbprint:
- Partner Center product `9PBDS94C8XD0`, submission ID and upload results:

- [ ] Compare current Partner Center Product Identity against the manifest's
  package name, publisher, and display name. A draft submission is confirmed
  by user screenshots; final account-verification status has not been inspected.
- [ ] Run the Windows build and retain MakeAppx validation, STORE-002 payload
  inspection, and staged frozen-render reports for the exact candidate.
- [ ] Download the Store artifact, verify both MSIX checksum entries, and verify
  GitHub provenance for MSIX, sources, and the MSIX checksum file.
- [ ] Review installed licenses and the matching native source archive; retain
  the human source/license approval required by the shared
  [Windows qualification](windows_preview_qualification.md#artifact-and-source-review).
- [ ] Publish and verify durable public source/build-instruction links for this
  exact Store version before it is distributed. Record retention for old versions.

## Installed MSIX checks

Follow [the local test procedure](../docs/06-building-and-releasing.md#local-msix-installation-and-verification)
on Windows 10 22H2 or Windows 11 x64. A staged EXE launch is not an MSIX install.

- [ ] Install the separately test-signed package for a standard user. Record any
  required administrator action for the temporary certificate trust.
- [ ] Run `scripts\verify_windows_msix.ps1` in Windows PowerShell 5.1. Retain
  STORE-003 and WIN-405 reports proving the installed identity and bundled
  preview, silent/audio rendering, dimensions/duration/codecs, and full decoding.
- [ ] Launch normally from Start; inspect Explorer/Start/taskbar icons and
  confirm no child console flashes during preview or render.
- [ ] Use **Save sample CSV...** to save and select a copy in Documents, including
  paths with spaces/Unicode/apostrophes. Edit the copy and reload it. Cancel an
  export and decline an overwrite; confirm existing files/selection are preserved.
- [ ] Choose real user videos, CSVs, output, and retained-overlay folders with
  dialogs. Confirm protected install files remain unchanged and temporary
  previews/overlays/partial renders are cleaned up outside the installation.
- [ ] Render with and without audio, inspect playback, question/answer effects,
  duration, readability, final frames, and sound in a normal Windows player.
- [ ] Exercise cancellation in both phases, overwrite decline/success, and a
  locked-output failure/retry. Preserve the previous output on failure/cancel.
- [ ] Check Main/Advanced/Questions, dialogs, progress, previews, and sample
  export at 100%, 125%, 150%, and 200% DPI; retain screenshots/results.
- [ ] Install a higher four-part version over an older candidate, then launch
  and render. Record both hashes/versions; a same-version reinstall is insufficient.
- [ ] Uninstall via Settings and confirm user videos/CSVs/outputs/retained
  overlays survive. Remove only the temporary test certificates and test copies.
- [ ] Retain separate-live-system results/sign-off and shared source/license
  approval; [the existing Windows environment blocker](port_to_windows.md#blocker-register)
  still applies. EXE-specific installer steps do not replace these MSIX checks.

## Certification and Store installation

- [ ] Run applicable Windows App Certification Kit checks on the installed/test
  package. Retain full results and explanations/resolutions for reported failures.
- [ ] Complete free pricing/markets, properties/category, age-rating answers,
  description/screenshots/assets, privacy/support and source/license materials.
  Explain `runFullTrust`: this is the existing medium-integrity desktop GUI with
  bundled FFmpeg subprocesses, not an elevated application or AppContainer app.
- [ ] Confirm account verification/submission eligibility in Partner Center.
- [ ] Upload the **original CI MSIX** to the draft, record package validation
  results and exact artifact/source identities, then obtain maintainer approval
  before submitting for certification. Local test signing changes the file hash.
- [ ] Record certification outcome separately from successful upload. Resolve
  feedback, obtain publication approval, and record the public listing URL.
- [ ] Install the actual Store-signed release and repeat Start launch, sample
  export, preview/render/playback; test a later Store update when available.

Approval, date, approved hashes, public source URL, and remaining caveats:

**Pending.**
