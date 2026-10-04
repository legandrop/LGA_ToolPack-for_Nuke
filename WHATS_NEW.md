# What's new in LGA ToolPack

## v2.66 (2026-10-04)

- **New:** Write Presets can now save your own presets: select a Write together with the nodes above it (color transforms, burn-ins, a backdrop) and press Alt+Shift+W, and that whole setup appears at the end of the Shift+W list, ready to paste under any node in any script.
- **New:** When you paste one of your own Write Presets, its CDL and LUT nodes load the look files of the shot you are working on, taken from that shot's .amf.
- **New:** You can share your own Write Presets: drag one from the Shift+W list to your desktop, a folder or a chat to get it as a .nk file, and drop a .nk from your file browser onto the list to add it to yours. Right-click one to move it to the trash.
- **New:** Reset Workspace is now also available in Hiero and Nuke Studio, from a TP menu (Ctrl+Alt+W).
- **New:** Snapshot Gallery's Shift+click, which opens a snapshot in FrameRev to annotate it, now works on macOS too. (macOS only)
- **Improved:** Write Presets' path review window opens where the presets list was, instead of in the middle of the screen.
- **Improved:** Media Manager no longer scans unrelated folders when a script is saved outside a shot, so it opens instantly.
- **Improved:** Snapshot Gallery's Shift+click opens the snapshot in FrameRev to annotate it, instead of the ShareX image editor that came with HieroTools, so it no longer needs HieroTools. It requires FrameRev 0.265 or later.
- **Fixed:** Write Presets' preRender + Switch creates an LGA backdrop again, placed above the backdrops already in the Node Graph.
- **Fixed:** Build Grade, Build Merge, Build RotoBlur, Iteration, Channels Cycle, Rotate Transform and Read to Project no longer act on a node left selected inside a gizmo when nothing is selected in the Node Graph.
- **Fixed:** With nothing selected, Write Presets creates the Write in the middle of the Node Graph view, instead of always in the same spot and connected to a node inside a gizmo.
