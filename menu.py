import nuke

if not (nuke.env["hiero"] or nuke.env["studio"]):
    import LGA_ToolPack_menu
