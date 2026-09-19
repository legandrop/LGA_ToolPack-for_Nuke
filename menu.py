import nuke

if not (nuke.env["hiero"] or nuke.env["studio"]):
    import LGA_ToolPack_menu
else:
    # En Hiero y Nuke Studio solo entra la lista blanca de HIERO_TOOLS.
    import LGA_ToolPack_Hiero_menu
