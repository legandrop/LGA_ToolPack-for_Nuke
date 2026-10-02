---
product: LGA ToolPack
release_repo: legandrop/LGA_ToolPack-for_Nuke
tech_changelog: ChangeLog.md
version_heading: "## v{v}"
platforms: [win, mac]
---
# What's new in LGA ToolPack
<!-- Editable while a version is unpublished. NOT append-only. Published versions are frozen. -->

## Unreleased

## v2.66
- [improved] Write Presets' path review window opens where the presets list was, instead of in the middle of the screen.
- [new] Write Presets can save your own presets: select a Write and the nodes above it, press Alt+Shift+W, and the whole chain appears in the Shift+W list, ready to paste under any node. To share one, drag it out of the list as a .nk file, and drop a .nk on the list to add it. When pasted, its CDL and LUT load the shot's own look files from the .amf, and its backdrops land above the ones already there.
- [fixed] Write Presets' preRender + Switch creates an LGA backdrop again, placed above the backdrops already in the Node Graph.
- [fixed] Build Grade, Build Merge, Build RotoBlur, Iteration, Channels Cycle, Rotate Transform and Read to Project no longer act on a node left selected inside a gizmo when nothing is selected in the Node Graph.
- [fixed] With nothing selected, Write Presets creates the Write in the middle of the Node Graph view, instead of always in the same spot and connected to a node inside a gizmo.
- [improved] Media Manager no longer scans unrelated folders when a script is saved outside a shot, so it opens instantly.
- [new] Reset Workspace is now also available in Hiero and Nuke Studio, from a TP menu (Ctrl+Alt+W).
- [improved] Snapshot Gallery's Shift+click opens the snapshot in FrameRev to annotate it, instead of the ShareX image editor that came with HieroTools, so it no longer needs HieroTools. It requires FrameRev 0.265 or later.
- [new][mac] Snapshot Gallery's Shift+click, which opens a snapshot in FrameRev to annotate it, now works on macOS too.
