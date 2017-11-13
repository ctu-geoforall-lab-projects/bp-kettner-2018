#!/usr/bin/env python

import os
import sys
import sqlite3

from osgeo import ogr

class VFKParBuilderError(Exception):
    pass

class VFKParBuilder:
    def __init__(self, filename):
        """Constructor VFKParBuilder

        :param str filename: path to VFK file
        """
        self.filename = filename

    def get_par(self):
        """Metoda vracejici seznam parcel pomoci SQL dotazu na databazi"""
        # Zjistim seznam parcel  - cislo kazde parcely jen jednou - unikatni seznam
        # zdroj: http://zetcode.com/db/sqlitepythontutorial/
        db = sqlite3.connect(os.path.splitext(self.filename)[0] + '.db')
        if db is None:
            raise VFKParBuilderError('Databaze nepripojena')
        parcely = []
        
        cur = db.cursor()
        cur.execute('SELECT par_id_1 as id FROM hp UNION SELECT par_id_2 as id from hp')
        while True:
            row = cur.fetchone()
            if row == None:
                break
            parcely.append(row[0])
        db.close()
        
        return parcely

    def filter_hp(self, id_par): #, lyr_hp):
        """Otevre soubor s daty, vezme vrstvu HP (lyr_hp) a najde vsechny hranice zadane parcely(id_par),
             neusporadane"""
        #DataSource
        ds = ogr.Open(self.filename)
        if ds is None:
            sys.exit('Nelze otevrit datasource')
        # Data v bloku HP
        lyr_hp = ds.GetLayerByName('HP')  # definice globalni promenne
        if lyr_hp is None:
            sys.exit('Nelze nacist vrstvu HP')
        #Filter hranic zadane parcely
        hp_list = []
        lyr_hp.SetAttributeFilter("PAR_ID_1 = '{0}' or PAR_ID_2 = '{0}'".format(id_par))
        for feat in lyr_hp:
            hp_list.append(feat)
        lyr_hp.SetAttributeFilter(None)
        #Odstraneni pripojeni k souboru
        del ds

        return hp_list #jen prvky ve vrstve, nikoliv geometrie (ta je oznacena list_hp)

    def build_par(self, id_par, list_hp):
        """Vrati geometrie dane parcely sestavenou geometrickou cestou"""
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

        # poc = 0
        while len(list_hp) > 0:  # sestavuju dokud mam v seznamu nejake hranice
            for poradi in range(len(list_hp)):
                if search in list_hp[poradi]:
                    # print "Poradi nalezene hranice: ",poradi,"Pozice bodu: ", list_hp[poradi].index(search)
                    # print "Vypis nalezene hranice: ", list_hp[poradi]
                    if (list_hp[poradi].index(search)) == 0:  # hranice orientovana stejne jako prvni pridana
                        self.add_boundary(poradi, 'front', list_hp, ring)
                        search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))
                        break
                    if (list_hp[poradi].index(search)) > 0:  # hranice ma opacnou orientaci
                        self.add_boundary(poradi, 'back', list_hp, ring)
                        search = (ring.GetX(ring.GetPointCount() - 1), ring.GetY(ring.GetPointCount() - 1))
                        break
                        # else:
                        # print "Pocet proslych hranic bez hledaneho bodu: ", poc
                        # poc = poc + 1
        # Create polygon
        poly_geom = ogr.Geometry(ogr.wkbPolygon)
        poly_geom.AddGeometry(ring)

        return poly_geom

    def add_boundary(self,index,direction, list_hp, ring):
        """Prida hranici parcely do ringu"""
        hranice = list_hp[index]
        prvni = (ring.GetX(0), ring.GetY(0))  # pocatecni bod ringu, pri uzavreni polygonu neni pridan(uz v hranici je)
        if direction == 'front':
            for i in range(1, len(hranice)):
                bod = hranice[i]
                if bod == prvni:  # pri pridavani posledni hranice neprida znovu prvni bod
                    break
                ring.AddPoint(bod[0], bod[1])
        if direction == 'back':
            for i in range(len(hranice) - 2, -1, -1):
                bod = hranice[i]
                if bod == prvni:
                    break
                ring.AddPoint(bod[0], bod[1])
        list_hp.pop(index)
        return ring

    def build_all(self, limit = 10):
        """Sestavovani vsech parcel postupne podle poradi v unikatnim seznamu"""
        counter = 0

        # get list of unique par ids
        parcely = self.get_par()
                    
        for par_id in parcely:
            list_hp = [] # vytvoreni prazdneho seznamu pro ulozeni hranic sestavovane parcely

            # collect unsorted list of vertices forming par boundary
            for feature in self.filter_hp(par_id):
                geom = feature.GetGeometryRef()
                list_hp.append(geom.GetPoints()) # seznam hranic parcel - jiz geometrie

            # create par geometry
            poly_geom = self.build_par(par_id, list_hp)

            # print result to stdout and check limit (will be removed)
            print (par_id, poly_geom.ExportToWkt())
            counter += 1
            if counter > limit:
                break

    def writeDB(self):
        """Ulozeni geometrii do databaze"""
        pass

#Funkcnost tridy
object = VFKParBuilder('600016.vfk')
#object.get_par()
#object.filter_hp(706860403)
object.build_all(3)
#print(object.add_boundary.__doc__) #vypis dokumentacniho retezce
