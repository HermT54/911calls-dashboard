from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from tkinter import *
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import requests
import mysql.connector
import datetime
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class createDashBoard():

    #THIS FUNCTION WILL BUILD THE FRAME/WINDOW
    def __init__(self, parent):

        #NEED A MENU SO I CAN CLOSE THE PROGRAM
        menu = Menu(root)
        root.config(menu=menu)
        fMenu = Menu(menu)
        fMenu.add_command(label='Exit', command = self.clientExit)
        fMenu.add_command(label='Append Data', command = dataManagement.AppendData)
        menu.add_cascade(label='File', menu = fMenu)
        edit = Menu(menu)

        #CREATE THE FIGURE AND ADD THE TWO PLOTS
        self.figure1, (self.lineChartPlot, self.mapPlot) = plt.subplots(1,2)
        #ADD THE TWO PLOTS TO THE CANVAS WHICH IS THE WINDOW
        self.canvas = FigureCanvasTkAgg(self.figure1, root)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)

        self.setupEntryBox()
        self.setupListBox()
        self.initialCalcData()

    def setupEntryBox(self):

        #CREATE THE ENTRY BOX AND ADD THAT TO THE CANVAS
        self.entrythingy = Entry(root)
        self.contents = StringVar()
        self.contents.set("ENTER ADDRESS: ")
        self.entrythingy["textvariable"] = self.contents
        self.entrythingy.bind('<Return>', self.getAddrString)
        self.entrythingy.pack(ipady=10)


    def setupListBox(self):
        #CREATE A LIST BOX FOR THE OUTPUT
        self.scrollListFrame = Frame()
        self.scrollListFrame.pack(side=LEFT, fill=Y)
        self.lb= Listbox(self.scrollListFrame)
        self.scrollbar = Scrollbar(self.scrollListFrame, command=self.lb.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.lb.config(yscrollcommand=self.scrollbar.set)
        self.lb.pack(expand=0, fill='y', anchor='w')
        self.lb.config(width=35)


    def initialCalcData(self):
        #CREATE GRAPH OF DATA FROM DATABASE AND PRE-POPULATE
        myCursor = "SELECT count, cfs_violent_indicator FROM violent_view"
        curResults = dataManagement.pullCursors(self, myCursor, None)
        xList, yList = zip(*curResults)
        y_pos = np.arange(len(yList))
        self.lineChartPlot.set_xticklabels(yList)
        self.lineChartPlot.set_xticks(y_pos, minor=False)
        self.lineChartPlot.set_ylabel('Number of Calls')
        self.lineChartPlot.bar(y_pos, xList, width=0.7, align="center")

        #GET THE BASEMAP
        getMyMap = baseMapObject.__init__(self, self.mapPlot)


    def clientExit(self):
        exit()


    def getAddrString(self, event):
        addInput = self.entrythingy.get()

        if addInput.find('/') == False:
            ai = baseMapObject.plotPoint(self, addInput)

        if addInput[0].isdigit():
            spcPos = addInput.find(' ') + 1
            myCursor = """SELECT COUNT(cfs_id), cfs_call_reason
                          FROM callsforservice
                          WHERE LOCATE(lower("%s"), lower(cfs_address1)) > 0
                          and LOCATE(lower("%s"), lower(cfs_address1)) > 0
                          GROUP BY cfs_call_reason""" % (addInput[0], addInput[spcPos:])
        elif addInput.find('/'):
            slshPos = addInput.find('/')
            print(addInput, slshPos, addInput[0:slshPos-1], addInput[slshPos+1:])
            myCursor = """SELECT COUNT(cfs_id), cfs_call_reason
                          FROM callsforservice
                          WHERE LOCATE(lower(trim("%s")), lower(trim(cfs_address1))) > 0
                          and LOCATE(lower(trim("%s")), lower(trim(cfs_address2))) > 0
                          GROUP BY cfs_call_reason""" % (addInput[0:slshPos-1], addInput[slshPos+1:])

        curResults = dataManagement.pullCursors(self, myCursor, None)
        createDashBoard.populateListBox(self, curResults)


    def populateListBox(self, curResults):


        try:
            ttlList = sum(1 for i in curResults)
            print(ttlList)
            self.lb.delete(1)
            for j in range(0, ttlList):
                self.lb.insert(END, curResults[j])
        except TypeError:
            self.lb.insert(END, "No Reports")


    def refreshCanvas(self, newMapPoint):
        self.canvas.draw()
        self.contents.set("ENTER ADDRESS: ")


#NOW CREATE A MAP OBJECT SINCE WILL MANIPULATE MAP
class baseMapObject():

    def __init__(self, mapPlot):

        #THIS IS THE IMPORTING OF THE CITY BLOCK SHAPEFILE
        self.map = Basemap(llcrnrlon = -90.32056203014196, llcrnrlat = 38.53356086640576, urcrnrlon=-90.17512027018158, urcrnrlat=38.77433955009363,
                      width=12, height=2, projection='lcc', lat_0=35.83, lon_0=-90.5, resolution=None, fix_aspect=False, ax=self.mapPlot)
        self.map.readshapefile("C:\\Users\\kelma_000\\Desktop\\Shapefiles\\STLCityBlocks\\STLBlocks", name='stlblock')

        self.axins = inset_axes(self.mapPlot, 1,1, loc=2)
        x,y = (0,0)
        self.plotHandle, = self.map.plot(x,y, marker='o', color='Red', markersize=8)
        plt.xticks(visible=False)
        plt.yticks(visible=False)

        return map


    def insetMapObject(self, loc):
        self.axins.clear()
        x1,y1 = (loc.longitude, loc.latitude)

        map2 = Basemap(llcrnrlon=(x1-0.006), llcrnrlat= (y1-0.006), urcrnrlon= (x1+0.006), urcrnrlat=(y1+0.006),
                       projection='lcc', lat_0=y1, lon_0=x1, resolution=None, fix_aspect=False, ax=self.axins)
        map2.readshapefile("C:\\Users\\kelma_000\\Desktop\\Shapefiles\\STLCityBlocks\\STLBlocks", name='stlblock2')
        x,y = map2(x1, y1)
        xS,yS = map2(x1-0.006, y1-0.006)
        xE,yE = map2(x1+0.006, y1+0.006)

        self.axins.set_xlim(xS,xE)
        self.axins.set_ylim(yS,yE)

        newMapPoint = map2.plot(x,y, marker = 'o', color='Red', markersize = 8)
        x,y = self.map(x1,y1)
        self.plotHandle.set_ydata(y)
        self.plotHandle.set_xdata(x)
        createDashBoard.refreshCanvas(self, newMapPoint)


    def plotPoint(self, addr1):

        #SINCE WON'T FIND AVE IF GIVEN STREET NEED TO HANDLE THAT
        geolocator = Nominatim()
        callloc = addr1 + ", Saint Louis, MO"
        loc = geolocator.geocode(callloc)
        if (loc == None):
            if (addr1.lower().rfind("ave") != -1):
                loc = geolocator.geocode(callloc.replace("ave", "st"))
            elif (addr1.lower().rfind("st") != -1):
                loc = geolocator.geocode(callloc.replace("st", "ave"))

        self.mapPlot = baseMapObject.insetMapObject(self, loc)
        self.contents.set("Address: ")


class dataManagement():

    def pullCursors(self, myCursor, addtlVar):

        cnx = mysql.connector.connect(user='root', database='analytics_911')
        cursor = cnx.cursor()

        cursor.execute(myCursor)
        curResults = list(cursor.fetchall())

        cnx.commit()

        cursor.close
        cnx.close

        return curResults

    def AppendData():

        cnx = mysql.connector.connect(user='root', database='analytics_911')
        cursor = cnx.cursor()

        cBquery = ("""SELECT COUNT(cfs_id) FROM callsforservice""")
        checkBefore = cursor.execute(cBquery)
        resultCheckBefore = cursor.fetchall()
        print(resultCheckBefore)

        htmlPage = requests.get("http://www.slmpd.org/cfs.aspx").text

        soup = BeautifulSoup(htmlPage, 'html.parser')

        cfsUpdate = soup.find(id="lblLastUpdate").text
        cfsUpdateStart = cfsUpdate.find(":") + 2
        cfsUpdateEnd = cfsUpdate.find("(")-4
        cfsUpdate2 = cfsUpdate[cfsUpdateStart:cfsUpdateEnd]
        try:
            cfsUpdatetime = datetime.strptime(cfsUpdate2, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            cfsUpdatetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cfsDates=[]
        cfsId=[]
        cfsAddr=[]
        cfsReason=[]

        table1 = soup.find("table")
        tableBody = table1.find_all('tr')

        for row in tableBody:
            cols = row.find_all('td')
            cfsDates.append(cols[0].get_text())
            cfsId.append(cols[1].get_text())
            cfsAddr.append(cols[2].get_text())
            cfsReason.append(cols[3].get_text())

        cfsAddr1 = []
        cfsAddr2 = []

        for ea in cfsAddr:
            posSep = ea.find('/')
            if posSep == -1:
                cfsAddr1.append(ea)
            else:
                newEnd = posSep-1
                newStart = posSep+1
                lenStr = len(ea)
                cfsAddr1.append(ea[0:newEnd])
                cfsAddr2.append(ea[newStart:lenStr])

        cfsDates2=[]
        cfsAddr3=[]

        ins911query = ("""INSERT INTO temp_junk(id, date1, addr1, addr2, reason, date2) VALUES (%s,%s,%s,%s,%s,%s)""")

        ttlCount = sum(1 for i in cfsId)
        for j in range(0,ttlCount):
            try:
                cfsDates2.append(datetime.strptime(cfsDates[j], "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                cfsDates2.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            try:
                var4 = cfsAddr2[j]
            except IndexError:
                var4 = None

            cursor.execute(ins911query, (cfsId[j], cfsDates2[j], cfsAddr1[j], var4, cfsReason[j], cfsUpdatetime))
            cnx.commit()

        appendQuery = ("""INSERT INTO callsforservice(cfs_id, cfs_date, cfs_address1, cfs_address2, cfs_call_reason, ods_updatetime)
                          SELECT b.id, b.date1, b.addr1, b.addr2, b.reason, b.date2 FROM temp_junk b
                          LEFT JOIN callsforservice a ON b.id = a.cfs_ID WHERE a.cfs_id IS NULL """)
        cursor.execute(appendQuery)
        cnx.commit()

        cAquery = ("""SELECT COUNT(cfs_id) FROM callsforservice""")
        checkAfter = cursor.execute(cAquery)
        resultCheckAfter = cursor.fetchall()
        print(resultCheckAfter)

        if resultCheckBefore == resultCheckAfter:
            print("No data appended")
        elif resultCheckAfter > resultCheckBefore:
            print("Data Appended")

        cursor.close
        cnx.close


if __name__ == '__main__':
    root = Tk()
    createDashBoard(root)
    root.mainloop()
