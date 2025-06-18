'''

duplicateWithInputs V1.1

copyright 2018 Marcel Pichert

www.marcelpichert.com

'''

import nuke
import nukescripts



def copyWithInputs():

    #get selected nodes

    global nodesWithInputs

    nodesWithInputs = nuke.selectedNodes()


def pasteWithInputs():
    
    try:
        nodes = nodesWithInputs
        
    except:
        nodes = "None"

    #check if at least one node is selected
    
    if len(nodes) != 0 and nodes != "None":
        
        #duplicate nodes

        newNodes = []

        for n in nodes:

            nuke.selectAll()
            nuke.invertSelection()

            n.setSelected(True)

            nukescripts.node_copypaste()

            newNodes.append(nuke.selectedNode())


        #set variables

        oldStartX = nodes[0].xpos()
        oldStartY = nodes[0].ypos()

        newStartX = newNodes[0].xpos()
        newStartY = newNodes[0].ypos()


        #position new nodes

        for i,x in enumerate(newNodes):

            if i != 0:

                offsetX = nodes[i].xpos() - oldStartX
                offsetY = nodes[i].ypos() - oldStartY

                x.setXYpos(newStartX + offsetX, newStartY + offsetY)

            #reconnect inputs

            for s in range(nodes[i].inputs()):

                try:
                    inputNode = newNodes[nodes.index(nodes[i].input(s))]

                except ValueError:
                    inputNode = nodes[i].input(s)

                x.setInput(s, inputNode)
                
            x.setSelected(True)
                

def duplicateWithInputs():

    copyWithInputs()

    pasteWithInputs()