#!/usr/bin/env python

import sys
import sqlite3

from osgeo import ogr

def filter_hp(lyr_hp, id_par):
    """Vezme vrstvu HP (lyr_hp) a najde vsechny hranice zadane parcely(id_par),
     neusporadane"""
    hp_list = []
    lyr_hp.SetAttributeFilter("PAR_ID_1 = '{0}' or PAR_ID_2 = '{0}'".format(id_par))
    for feat in lyr_hp:
        hp_list.append(feat)
    
    lyr_hp.SetAttributeFilter(None)
    
    return hp_list

def add_boundary(index,direction,list_hp,ring):
    """Prida hranici parcely do ringu"""
    hranice = list_hp[index]
    prvni = (ring.GetX(0), ring.GetY(0)) #pocatecni bod ringu, pri uzavreni polygonu neni pridan(uz v hranici je)
    if direction =='front':
        for i in range(1,len(hranice)):
            bod = hranice[i]
            if bod == prvni: #pri pridavani posledni hranice neprida znovu prvni bod
                break
            ring.AddPoint(bod[0], bod[1])
    if direction == 'back':
        for i in range(len(hranice)-2,-1,-1):
            bod = hranice[i]
            if bod == prvni:
                break
            ring.AddPoint(bod[0], bod[1])
    list_hp.pop(index)

def build_par(id_par, list_hp):
    """Vrati geometrie dane parcely"""
    ##SESTAVENI POLYGONU GEOMETRICKOU CESTOU

    # vytvoreni ringu
    ring = ogr.Geometry(ogr.wkbLinearRing)

    # Pridam prvni linii a smazu ji v seznamu hranic
    hranice_1 = list_hp[0]
    for i in range(len(hranice_1)):
        bod = hranice_1[i]
        ring.AddPoint(bod[0], bod[1])
    list_hp.pop(0)

    # Pridani dalsich linii hranice
    # Hledani koncoveho bodu ringu v seznamu hranic - prvni hledany bod
    search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))  # koncovy bod

    #poc = 0
    while len(list_hp) > 0: #sestavuju dokud mam v seznamu nejake hranice
        for poradi in range(len(list_hp)):
            if search in list_hp[poradi]:
                # print "Poradi nalezene hranice: ",poradi,"Pozice bodu: ", list_hp[poradi].index(search)
                # print "Vypis nalezene hranice: ", list_hp[poradi]
                if (list_hp[poradi].index(search)) == 0:  # hranice orientovana stejne jako prvni pridana
                    add_boundary(poradi, 'front', list_hp, ring)
                    search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))
                    break
                if (list_hp[poradi].index(search)) > 0:  # hranice ma opacnou orientaci
                    add_boundary(poradi, 'back', list_hp, ring)
                    search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))
                    break
            # else:
                # print "Pocet proslych hranic bez hledaneho bodu: ", poc
                #poc = poc + 1
    # Create polygon
    poly_geom = ogr.Geometry(ogr.wkbPolygon)
    poly_geom.AddGeometry(ring)

    print id_par, poly_geom.ExportToWkt()
    
ds = ogr.Open('600016.vfk')
if ds is None:
    sys.exit('Nelze otevrit datasource')

#Zjistim seznam parcel  - cislo kazde parcely jen jednou - unikatni seznam
#zdroj: http://zetcode.com/db/sqlitepythontutorial/
db = sqlite3.connect('600016.db')
if db is None:
    sys.exit('Databaze nepripojena')
parcely = []
with db:
    cur = db.cursor()
    cur.execute('SELECT par_id_1 as id FROM hp UNION SELECT par_id_2 as id from hp')
    while True:
        row = cur.fetchone()
        if row == None:
            break
        parcely.append(row[0])
if db:
        db.close()
print "Pocet parcel: ", len(parcely)

### HP
lyr_hp = ds.GetLayerByName('HP')
if lyr_hp is None:
    sys.exit('Nelze nacist vrstvu HP')

#Sestavovani parcel postupne podle poradi v unikatnim seznamu
for i in range(10):#(len(parcely)):
    list_hp = [] #vytvoreni prazdneho seznamu pro ulozeni hranic sestavovane parcely
    id = parcely[i]
    for feature in filter_hp(lyr_hp, id):
        geom = feature.GetGeometryRef()
        list_hp.append(geom.GetPoints()) # seznam hranic parcel
    build_par(id,list_hp)

del ds
