# Visualisation de cendres sur une carte
Voici mon projet de bachelor. Il permet d'afficher des dépôts de particules contenus dans un fichier *.h5* sur une carte provenant d'un fichier *.tiff*.

Voici un exemple d'utilisation:  
`
	./view.py --img file_exemple/map_ruapeu.tif --ash file_exemple/r90u40d1000da4500.h5 --posx 175.56 --posy -39.26 --alpha 0.5
`

Vous remarquerez que le *map_ruapeu.tif* a été compressé pour ne pas dépasser la taille maximale de fichier autorisé par Github. Avant de tester, il faudra donc extraire l'image.

Il est à noté qu'en appelant:
`
 ./view.py --help
 `
 
Vous obtiendrez le détail des paramètres.  
Le projet est écrit en Python2.7, en voici les dépendances:

* argparse
* gdal
* h5py
* math
* matplotlib
* numpy
* scipy
* sys 
