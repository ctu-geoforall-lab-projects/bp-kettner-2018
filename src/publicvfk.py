#!/usr/bin/env python

import sys

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
    prvni = (ring.GetX(0), ring.GetY(0))
    if direction =='front':
        for i in range(1,len(hranice)):
            bod = hranice[i]
            if bod == prvni: #pri pridavani posledni hranice neprida znovu prvni bod
                break
            ring.AddPoint(bod[0], bod[1])
    if direction == 'back':
        for i in range(len(hranice)-1,0,-1):
            bod = hranice[i]
            if bod == prvni:
                break
            ring.AddPoint(bod[0], bod[1])
    list_hp.pop(index)

def build_par(id_par, list_hp):
    """Vrati geometrie dane parcely"""
    # TODO
    # https://pcjericks.github.io/py-gdalogr-cookbook/geometry.html#create-a-polygon
    # Postup:
    # 1. vytvorit prazdnou geometrii pro polygon 
    # 2. pro kazdy prvek z list_hp zjistit geometrii (GetGeometryRef)
    # 3. geometrii prvku pridat do polygonu
    # 4. return id_par, geom_poly

    ##SESTAVENI POLYGONU GEOMETRICKOU CESTOU
    # create ring - geometrie vnejsi hranice

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
    while len(list_hp) > 0:
        for poradi in range(len(list_hp)):
            if search in list_hp[poradi]:
                # print "Poradi nalezene hranice: ",poradi,"Pozice bodu: ", list_hp[poradi].index(search)
                # print "Vypis nalezene hranice: ", list_hp[poradi]
                if (list_hp[poradi].index(search)) == 0:  # hranice orientovana stejne jako prvni pridana
                    add_boundary(poradi, 'front', list_hp, ring)
                    search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))
                    break
                if (list_hp[poradi].index(search)) > 0:  # hranice ma opcanou orientaci
                    add_boundary(poradi, 'back', list_hp, ring)
                    search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))
                    break
            # else:
                # print "Pocet proslych hranic bez hledaneho bodu: ", poc
                #poc = poc + 1
    # Create polygon
    poly_geom = ogr.Geometry(ogr.wkbPolygon)
    poly_geom.AddGeometry(ring)

    return id_par, poly_geom.ExportToWkt()
    
ds = ogr.Open('600016.vfk')
if ds is None:
    sys.exit('Nelze otevrit datasource')

#print ("Pocet vrstev: {}".format(ds.GetLayerCount()))

#Vypisovani nazvu vrstev
for idx in range(ds.GetLayerCount()):
    lyr = ds.GetLayerByIndex(idx)
    #print (lyr.GetName())

### HP
lyr_hp = ds.GetLayerByName('HP')
if lyr_hp is None:
    sys.exit('Nelze nacist vrstvu HP')

#co je v HP
##print ("Pocet prvku v HP: {}".format(lyr_hp.GetFeatureCount()))

# prochazet sekvencne prvky ve vrstve HP (hranice parcel)
i = 0
for id_hp in range(1, 100):#lyr_hp.GetFeatureCount()+1):
    i = i+1
    ##print ("Prvek cislo: {}".format(i))
    feat = lyr_hp.GetFeature(id_hp)
    # zjistit id parcel vlevo a vpravo
    id1 = feat.GetField('PAR_ID_1')
    id2 = feat.GetField('PAR_ID_2')
    print id1 #,id2
    # seznam linii - hranic parcel
    list_hp = []
    for feature in filter_hp(lyr_hp, id1):
        geom = feature.GetGeometryRef()
        #print ("Pocet bodu hranice: {}".format(geom.GetPointCount()))
        # seznam hranic parcel
        list_hp.append(geom.GetPoints())
        # vypis vsech bodu jedne hranice
        # print ("Body hranice: {}".format(geom.GetPoints()))
        # vypis koncovych a pocatecnich bodu hranice
    print "Pocet bodu linie", len(list_hp)

    # zpracovat prvni parcelu
    print ('1', build_par(id1, list_hp))
    # zpracovat druhou parcelu
    #print ('2', build_par(id2, list_hp_2))
    feat = None
    #break

#seznam linii - hranic parcel
list_hp = []
for feature in filter_hp(lyr_hp, id1):
    geom = feature.GetGeometryRef()
    ##print ("Pocet bodu hranice: {}".format(geom.GetPointCount()))
    #seznam hranic parcel
    list_hp.append(geom.GetPoints())
    # vypis vsech bodu jedne hranice
    #print ("Body hranice: {}".format(geom.GetPoints()))
    #vypis koncovych a pocatecnich bodu hranice
print ("Parcela: {} ma: {} hranic.".format(id1,len(list_hp)))
del ds