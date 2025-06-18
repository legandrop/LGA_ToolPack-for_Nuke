# Browse Directory v1.1, 2013-10-13
# by Fredrik Averpil, fredrik.averpil [at] gmail.com, http://fredrikaverpil.tumblr.com
# 
#
# Usage:
# a) select any Write node or Read node and run browseDirByNode()
# b) open any path via command browseDir(path)
# 
# Example of menu.py:
# import browseDir
# nuke.menu( 'Nuke' ).addCommand( 'My file menu/Browse/Node\'s file path', "browseDir.browseDirByNode()", 'shift+b' )
# nuke.menu( 'Nuke' ).addCommand( 'My file menu/Browse/Scripts folder', "browseDir.browseDir('scripts')" )
#
# And if your folder structure looks like this -
# serverpath/ ... sequence_folder/shot_folder/nuke/scripts/
# you should be able to use the following as well:
# nuke.menu( 'Nuke' ).addCommand( 'My file menu/Browse/Scripts folder', "browseDir.browseDir('sequence')" )
# nuke.menu( 'Nuke' ).addCommand( 'My file menu/Browse/Scripts folder', "browseDir.browseDir('shot')" )
#
#



import nuke
import sys
import os

def launch(directory):
	# Open folder
	print('Attempting to open folder: ' + directory)
	if os.path.exists( directory ):
		if(sys.platform == 'win32'):
			os.startfile(directory)
		elif(sys.platform == 'darwin'):
			os.system('open "' + directory + '"')
	else:
		nuke.message('Path does not exist:\n' + directory)


def browseDirByNode():

	error = False

	try:
		selectedNodeFilePath = nuke.callbacks.filenameFilter( nuke.selectedNode()['file'].evaluate() )
		folderPath = selectedNodeFilePath[ : selectedNodeFilePath.rfind('/') ]
		launch(folderPath)
	except ValueError:
		error = True
		nuke.message('No node selected.')
	except NameError:
		error = True
		nuke.message('You must select a Read node or a Write node.')
	except:
		folder = nuke.root().name()
		folderPath = ('/').join(folder.split('/')[0:-2])
		folderPath = os.path.join(folderPath,'_output').replace('\\', '/')
		launch(folderPath)

