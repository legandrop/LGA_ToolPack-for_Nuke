"""
____________________________________________________________________________________

  LGA_Write_SendMail v1.0 | Lega
  Agrega a los nodos Write el boton para enviar mail
  Funciona en conjunto con el LGA_Write_RenderComplete
____________________________________________________________________________________
"""

import nuke


def add_send_mail_checkbox():
    for node in nuke.allNodes("Write"):
        if not node.knobs().get("send_mail"):
            send_mail_knob = nuke.Boolean_Knob("send_mail", "Send Mail")
            node.addKnob(send_mail_knob)
            node["send_mail"].setValue(False)
            node["send_mail"].setFlag(nuke.STARTLINE)


# Agregar el checkbox a cualquier nuevo nodo Write que se cree
def add_checkbox_to_new_write_nodes():
    node = nuke.thisNode()
    if node.Class() == "Write" and not node.knobs().get("send_mail"):
        send_mail_knob = nuke.Boolean_Knob("send_mail", "Send Mail")
        node.addKnob(send_mail_knob)
        node["send_mail"].setValue(False)
        node["send_mail"].setFlag(nuke.STARTLINE)


nuke.addOnUserCreate(add_checkbox_to_new_write_nodes, nodeClass="Write")
