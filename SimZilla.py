
#!/usr/bin/env python3
# coding: utf-8

from tkinter import *
from tkinter import messagebox
import pyodbc
import json


# load config
with open('SimZilla.config.json') as j:
# with open('./text.txt') as j:

    config = json.load(j)

    # sql database variables
    server = config['server']
    database = config['database'] 
    username = config['username'] 
    password = config['password'] 
    driver = config['driver'] 


# colors
open_loc = "#dfdfdf" # gray
occupied_loc_remove = "#528aaa" # blue
occupied_loc = "#d86a14" # orange

newline = "\n"




def create_circle(x, y, r, canvasName):  # center coordinates, radius
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvasName.create_oval(x0, y0, x1, y1, fill=open_loc)



# init our application's root window
root = Tk()
root.title("SimZilla")
root.geometry('800x350')
Grid.columnconfigure(root, 2, weight=1)

# init canvas area
w = Canvas(root,width=800, height=200, background='white')
w.pack()

# get location coordinates
coords = []
locRow = []

with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD=' + password) as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT TOP (1000) [LocationId],[LocationX],[LocationY] FROM [CEPHAS_Yamato].[dbo].[MRM_Loc_Data] WHERE LocationId > 0 and LocationId < 9000")
        row = cursor.fetchone()
        while row:
            locRow = [row[0], row[1], row[2]]
            coords.append(locRow)
            row = cursor.fetchone()


# locations list
locations = []

# render locs
count = 0
for i in coords:
    # get data from list
    data = i
    id = data[0]
    x = data[1]
    y = data[2]

    # scale to fit canvas
    x = (x/100)-520
    x = w.winfo_reqwidth() - x # flip x coord
    y = (y/100)

    # render location
    b = create_circle(x, y, 5, w)
    w.pack()

    # add to locations list
    locations.append(b)

    # bind click event
    w.tag_bind(
        locations[count],
        '<Button-1>',
        lambda e, x=count: occupy_remove(x)  # call change function
    )

    w.tag_bind(
        locations[count],
        '<Button-3>',
        lambda e, x=count: occupy(x)  # call change function
    )

    count = count + 1


# canvas text legend
# occupired for remove
w.create_text(400, 160,text="Roll on retrieval schedule", fill=occupied_loc_remove,font=("Helvetica 12 bold"))
# occupied
w.create_text(400, 185, text="Roll not on retrieval schedule", fill=occupied_loc,
              font=("Helvetica 12 bold"))


# change fill color
def occupy_remove(x):
    # get location fill
    tup = w.itemconfig(locations[x], 'fill')
    fill = tup[-1]
    # fill occupied/open
    if fill == open_loc:
        w.itemconfig(locations[x], fill=occupied_loc_remove)
    else:
        w.itemconfig(locations[x], fill=open_loc)

# change fill color
def occupy(x):
    # get location fill
    tup = w.itemconfig(locations[x], 'fill')
    fill = tup[-1]
    # fill occupied/open
    if fill == open_loc:
        w.itemconfig(locations[x], fill=occupied_loc)
    else:
        w.itemconfig(locations[x], fill=open_loc)



# clear yard
def clearYard():
    # for i in locations:
    for i in range(len(locations)):
        # tup = w.itemconfig(locations[i], 'fill')
        # fill = tup[-1]
        w.itemconfig(locations[i], fill=open_loc)

# output occupied locs
def save():
    # open files to write
    dir = "./"
    # dir = "C:/Nucor_Yamato_Cephas_Roll/Config/SimInputs/"
    id_trans = open(dir+"MRM_ID_Trans.sql", 'w')
    id_static = open(dir+"MRM_r_ID_Static.sql", 'w')
    sched_retrieve = open(dir+"Sim_Schedule_Retrieve.sql", 'w')
    # init db use
    id_trans.write("USE CEPHAS_Yamato"+newline +
                   "TRUNCATE TABLE MRM_ID_Trans"+newline)
    id_static.write("USE CEPHAS_Yamato"+newline+"TRUNCATE TABLE MRM_r_ID_Static"+newline +
                    "SET IDENTITY_INSERT [dbo].[MRM_r_ID_Static] ON"+newline+newline)
    sched_retrieve.write("USE CEPHAS_Yamato"+newline +
                         "TRUNCATE TABLE Sim_Schedule_Retrieve"+newline)

    count = 0
    inv_uid = 100
    sim_time = 0
    for x in coords:
        data = x
        id = data[0]
        tup = w.itemconfig(locations[count], 'fill')
        fill = tup[-1]
        # if fill == occupied_loc_remove:
        if fill != open_loc:
            # check location to get roll type
            if id in range(400, 516):
                rollType = 1
            else:
                rollType = 2
            
            id_trans.write(
                "INSERT[dbo].MRM_ID_Trans(Inv_Uid, [PickableID], LocationId) VALUES("+str(inv_uid)+", 1, "+str(id)+")"+newline)
                
            id_static.write(
                "INSERT [dbo].MRM_r_ID_Static (Inv_Uid,[Inv_Id],[OD],[Type],[Width]) VALUES ("+str(inv_uid)+", N'Roll_"+str(inv_uid)+"',40,"+str(rollType)+",88)"+newline)

            if fill == occupied_loc_remove: 
                sched_retrieve.write(
                    "INSERT [dbo].Sim_Schedule_Retrieve (Inv_Uid,simTime_s) VALUES ("+str(inv_uid)+","+str(sim_time)+")"+newline)

            inv_uid = inv_uid+1
            sim_time = sim_time+1410
        count = count+1
    id_trans.close()
    id_static.close()
    sched_retrieve.close()

    # small rolls outside yard for insert
    try:
        # get input
        test_input = inputNum_small.get()
        if test_input == "":
            rollsOutside_small = 0
        else:
            rollsOutside_small = int(inputNum_small.get())

        test_input = inputNum_large.get()
        if test_input == "":
            rollsOutside_large = 0
        else:            
            rollsOutside_large = int(inputNum_large.get())

    except:
        messagebox.showerror("Invalid input!","Input value must be an integer!")
        rollsOutside_small = 0
        rollsOutside_large = 0

    sim_time = 1190
    id_trans = open(dir+"MRM_ID_Trans.sql", 'a')
    id_static = open(dir+"MRM_r_ID_Static.sql", 'a')
    sched_insert = open(dir+"Sim_Schedule_Insert.sql", 'w')
    sched_insert.write("USE CEPHAS_Yamato"+newline +
                         "TRUNCATE TABLE Sim_Schedule_insert"+newline)

    for i in range(rollsOutside_small):
        rollType = 1
        id_trans.write(
            "INSERT[dbo].MRM_ID_Trans(Inv_Uid, [PickableID], LocationId) VALUES("+str(inv_uid)+", 1, -1)"+newline)

        id_static.write(
            "INSERT [dbo].MRM_r_ID_Static (Inv_Uid,[Inv_Id],[OD],[Type],[Width]) VALUES ("+str(inv_uid)+", N'Roll_"+str(inv_uid)+"',40,"+str(rollType)+",88)"+newline)

        sched_insert.write(
            "INSERT [dbo].Sim_Schedule_Insert (Inv_Uid,simTime_s) VALUES ("+str(inv_uid)+","+str(sim_time)+")"+newline)

        inv_uid = inv_uid+1
        sim_time = sim_time+3310

    for i in range(rollsOutside_large):
        rollType = 2
        id_trans.write(
            "INSERT[dbo].MRM_ID_Trans(Inv_Uid, [PickableID], LocationId) VALUES("+str(inv_uid)+", 1, -1)"+newline)

        id_static.write(
            "INSERT [dbo].MRM_r_ID_Static (Inv_Uid,[Inv_Id],[OD],[Type],[Width]) VALUES ("+str(inv_uid)+", N'Roll_"+str(inv_uid)+"',40,"+str(rollType)+",88)"+newline)

        sched_insert.write(
            "INSERT [dbo].Sim_Schedule_Insert (Inv_Uid,simTime_s) VALUES ("+str(inv_uid)+","+str(sim_time)+")"+newline)

        inv_uid = inv_uid+1
        sim_time = sim_time+3310

    id_trans.close()
    id_static.close()
    sched_insert.close()

    id_static = open(dir+"MRM_r_ID_Static.sql", 'a')
    id_static.write(newline+newline +
                    "SET IDENTITY_INSERT [dbo].[MRM_r_ID_Static] OFF")


# testing grid????
testLabel = Label(text="Left Click location to add roll on retrieval schedule"+newline+newline +
                  "Right Click location to add roll in yard," + newline+
                  "but not on retrieval schedule"+newline+newline +
                  "Outside rolls must be a valid whole number, or left blank")
# testLabel.grid(column=1, row=1)
testLabel.pack(side=LEFT)

testLabel2 = Label(text="Save Yard will store current layout, and save SQL files"+newline+newline +
                  "Clear Yard will clear current yard layout"+newline+newline)
# testLabel.grid(column=1, row=1)
testLabel2.pack(side=RIGHT)

# rolls outside yard
inputLabel_small = Label(text="Small Rolls Outside Yard")
inputLabel_small.pack()
inputNum_small = Entry(width=15)
inputNum_small.pack()

inputLabel_large = Label(text="Large Rolls Outside Yard")
inputLabel_large.pack()
inputNum_large = Entry(width=15)
inputNum_large.pack()




# print/save file button
saveButton = Button(root, text = "save yard", command = save)
saveButton.pack()

# clear button
clearButton = Button(root, text="clear yard", command=clearYard)
clearButton.pack()


# start a loop over the application
root.mainloop()
