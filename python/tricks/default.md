Python tricks 


Python cheat list
http://rgruet.free.fr/PQR26/PQR2.6.html
https://perso.limsi.fr/pointal/_media/python:cours:mementopython3-english.pdf
AddedBytes: http://www.addedbytes.com/cheat-sheets/python-cheat-sheet/
RichardGruet: http://rgruet.free.fr/PQR26/PQR2.6.html
http://rgruet.free.fr/PQR26/PQR2.6.html
http://rgruet.free.fr/PQR27/PQR2.7_printing_a4.pdf




text = 'Текст'
print(f"{text}")
print (f" {text:.^20}")

my_list = [5,9,0,5,4,7,9,5,3]
mpv = max (my_list, key=my_list.count)
print(mpv)


from pathlib import Path

for path, directories, files in Path('./code/tmp/one').walk():
    print(path, directories, files)

python3.12 -m uuid


Orm like Django and alchemy
https://github.com/collerek/ormar