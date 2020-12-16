from tkinter import *
import tkinter.messagebox
import tkinter.filedialog
import tkinter.simpledialog
from PIL import Image, ImageTk
import cv2
import math
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import numpy as np
import pathfinder_xi
import send_g_code
# import Camera_Calibration


class show_img:  # Funktion um Bild an zu zeigen
    def __init__(self, cv2image, ratio=0):
        ##Für Anzeige der CV2 Bilder in tkinter Canvas##
        cv2image, self.ratio = img_change_size(cv2image, ratio)  # enable/disable für anpassung der größe
        img = Image.fromarray(cv2image)  # Image in PIL
        self.imgtk = ImageTk.PhotoImage(image=img)  # Image in tkinter
        canvas.config(width=cv2image.shape[1], height=cv2image.shape[0])  # Größe canvas anpassen
        canvas.create_image(0, 0, image=self.imgtk, anchor=NW)  # Bild in Canvas schreiben
        self.cv2img2 = cv2image  # Bild für select_color kopieren
        status_bar.config(text='Bitte alle benötigten Größen eingeben')

        #self.color_RGB=[120,100,50] #Für Entwicklungszwecke Farbe festlegen
        #self.ratio=0.0236327 #Für Entwicklungszwecke skalierung festlegen
        cv2.imwrite('testbildTMP.png', cv2image)

        #Um ratio bei aufnahme von bildern fix zu halten
        self.fix_length = False
        if ratio != 0:
            self.fix_length = True

        def starten():
            BildMaskieren( cv2image, self.color_RGB, self.ratio, self.tattoo_shape, self.birthmarks)

        def TriggerToolbar(trigger):
            if str(Farbe['state']) == str(self.Laenge['state']) == str(Kontur['state']) == str(Auslassen['state']) == 'normal': #Bei aktivieren eines buttons
                Farbe.config(state='disabled')
                self.Laenge.config(state='disabled')
                Kontur.config(state='disabled')
                Auslassen.config(state='disabled')
                Start.config(state='disabled')
                menu.entryconfig("Datei", state="disabled") #Datei menü deaktivieren
                canvas.config(cursor="hand1") #Cursor zu Hand
                self.trigg_button = 'first' #Bei aktivieren eines buttons
            else: #Um restliche Buttons wieder zu aktivieren
                Farbe.config(state='normal')
                self.Laenge.config(state='normal')
                Kontur.config(state='normal')
                Auslassen.config(state='normal')
                menu.entryconfig("Datei", state="normal") #Datei menü aktivieren
                canvas.config(cursor="arrow") #Cursor zurück zu Pfeil
                self.trigg_button = 'second' #Bei deaktivieren der Buttons
                canvas.unbind('<Button-1>') #Löscht alle Bindungen von linker Maustaste
                try:
                    if self.ratio != 0 and self.color_RGB != [] and self.tattoo_shape != []:
                        Start.config(state='normal')
                        status_bar.config(text='Bereit')
                    else:
                        status_bar.config(text='Bitte alle benötigten Größen eingeben')
                except:
                    pass

            if trigger == 'farbe':
                Farbe.config(state='normal')
                self.select_color()
            elif trigger == 'laenge':
                self.Laenge.config(state='normal')
                ratio=self.length()
            elif trigger == 'kontur':
                Kontur.config(state='normal')
                self.select_shape()
            elif trigger == 'auslassen':
                Auslassen.config(state='normal')
                self.exclude()
            elif trigger == 'start':
                pass

        self.birthmarks=[]
        self.tattoo_shape=[]
        self.TriggerToolbar=TriggerToolbar #Um in length darauf zu zu greifen
        global toolbar
        toolbar.destroy()
        toolbar = Label(l)  # Erstellt leere Toolbar
        toolbar.pack(side=TOP, fill=X)
        Farbe = Button(toolbar, text='Farbe auswählen', command=lambda: TriggerToolbar('farbe'))
        Farbe.grid(row=0, column=1, padx=5, pady=1)
        self.Laenge = Button(toolbar, text='Skalierung festlegen', command=lambda: TriggerToolbar('laenge'))
        self.Laenge.grid(row=0, column=2, padx=5, pady=1)
        Kontur = Button(toolbar, text='Tattoo markieren', command=lambda: TriggerToolbar('kontur'))
        Kontur.grid(row=0, column=3, padx=5, pady=1)
        Auslassen = Button(toolbar, text='Stellen auslassen?', command=lambda: TriggerToolbar('auslassen'))
        Auslassen.grid(row=0, column=4, padx=5, pady=1)
        Start = Button(toolbar, text='Starten', command=starten)
        Start.grid(row=0, column=6, padx=5, pady=1)
        Start.config(state='disabled')
        self.cBOX = Label(toolbar, width=25)
        self.cBOX.grid(row=0, column=5, padx=5, pady=1)



    def select_color(self):
        def color(event):  # Zum auswählen der Hintergrunffarbe in Bild
            x = event.x  # cursor x-Position
            y = event.y  # cursor y-Position
            radius = 20
            R = G = B = i = 0
            for h in range(-radius, radius):
                for v in range(-radius, radius):
                    pass
                    R = R + self.cv2img2[y + v][x + h][0]
                    G = G + self.cv2img2[y + v][x + h][1]
                    B = B + self.cv2img2[y + v][x + h][2]
                    i = i + 1
            self.color_RGB = [int(R / i), int(G / i), int(B / i)]
            color_HEX = '#{:02x}{:02x}{:02x}'.format(self.color_RGB[0], self.color_RGB[1], self.color_RGB[2]) #RGB to HEX-code
            #print('Color-RGB:', self.color_RGB, 'Color-HEX:', color_HEX)
            self.cBOX.config(bg=color_HEX)
        if self.trigg_button== 'first':
            canvas.bind('<Button-1>', color) #Bindet linksklick an funktion



    def length(self):
        if self.fix_length: #Wenn bild aufgenommen wurde. Verhältniss festgesetzt
            tkinter.messagebox.showerror('Disabled', 'Bei Aufnahmen ist das Verhältniss fix')
        else: #Wenn bild aus galarie ausgewählt wurde
            def l(event):
                x = event.x  # cursor x-Position
                y = event.y  # cursor y-Position
                if self.old_coords == [0,0]:
                    self.old_coords = [x, y]
                    self.motion_track = canvas.bind('<Motion>', self.mouseMove)
                    self.myline = canvas.create_line(0, 0, 0, 0)
                    self.Laenge.config(state='disabled')
                else:
                    canvas.unbind('Motion', self.motion_track)
                    l_pixel = math.sqrt((int(canvas.canvasx(event.x)) - self.old_coords[0]) ** 2 + (int(canvas.canvasy(event.y)) - self.old_coords[1]) ** 2)  # Errechnet strecke
                    try:
                        l_real=tkinter.simpledialog.askfloat('Maßstab', 'Wie lang ist die gewählte Strecke? [mm]')
                        self.ratio=l_real/l_pixel
                        print(self.ratio)
                    except:
                        print('ERROR: Keine Skalierung festgelegt')
                    canvas.delete(self.myline)
                    self.old_coords = [0, 0]
                    self.TriggerToolbar('laenge') #Nach beenden des Dialogs werden buttons zurückgestzt

            self.old_coords = [0, 0]
            if self.trigg_button== 'first':
                canvas.bind('<Button-1>', l) #Bindet linksklick an funktion

    def select_shape(self):
        def cut(event):
            if self.alreadyDrawed:
                canvas.delete(self.polygon)
            x = event.x  # cursor x-Position
            y = event.y  # cursor y-Position
            self.old_coords = [x, y]  # Für mouseMove-Funktion
            self.motion_track = canvas.bind('<Motion>', self.mouseMove)  # Mousemove Funktion
            self.polygon_coords.append([x, y])  # Koordinaten für Polygon

            if len(
                    self.polygon_coords) == 2:  # Wenn zwei Punkte vorhanden: Zeichnet linien aus Klick-Koordinaten (erste Linie)
                for l in range(0, len(self.polygon_coords) - 1):
                    self.lines.append(canvas.create_line(self.polygon_coords[l], self.polygon_coords[l + 1], width=2))

            elif len(self.polygon_coords) > 2:  # wie if, nur das alte Linien gelöscht werden (zweite Linie)
                for line in self.lines:
                    canvas.delete(line)
                for l in range(0, len(self.polygon_coords) - 1):
                    self.lines.append(canvas.create_line(self.polygon_coords[l], self.polygon_coords[l + 1], width=2))
                if len(self.polygon_coords) > 2:  # Falls mehr als zwei Punkte ausgewählt wurden
                    if abs(self.polygon_coords[0][0] - x) < catch_range and abs(self.polygon_coords[0][
                                                                                    1] - y) < catch_range:  # Wenn neuer punkt nah genug an altem ist wird polygon geshclossen
                        self.polygon = canvas.create_polygon(self.polygon_coords, outline='black', fill='green',
                                                             stipple="gray12", width=3)
                        for line in self.lines:
                            canvas.delete(line)
                        self.tattoo_shape = self.polygon_coords
                        self.polygon_coords = []
                        canvas.unbind('Motion', self.motion_track)
                        self.alreadyDrawed = True

        self.alreadyDrawed = False  # Trigger ob schon Polygon existiert, welches gelöscht werden muss
        catch_range = 10  # Radius, in dem Polygon als geschlossen erkannt wird

        if self.trigg_button == 'first':  # Wenn button das erste mal geklickt wird bzw. bei allen ungeraden anzahlen
            try:
                canvas.delete(self.polygon)
            except:
                pass
            self.tattoo_shape = []
            canvas.bind('<Button-1>', cut)  # Bindet linksklick an funktion
            self.myline = canvas.create_line(0, 0, 0, 0)
            self.lines = []
            self.polygon = canvas.create_polygon([0, 0], [0, 0], [0, 0])
            self.polygon_coords = []
        else:  # Wenn button das zweite mal geklickt wird bzw. bei allen gerade anzahlen
            # canvas.delete(self.polygon)
            canvas.delete(self.myline)
            for line in self.lines:
                canvas.delete(line)
            try:
                canvas.unbind('Motion', self.motion_track)
            except:
                pass


    def exclude(self):
        def cut(event):
            #if self.alreadyDrawed_excl: #Löscht Polygon, falls es schon existiert
                #canvas.delete(self.polygon_excl)
            x = event.x  # cursor x-Position
            y = event.y  # cursor y-Position
            self.old_coords = [x, y]  # Für mouseMove-Funktion
            self.motion_track = canvas.bind('<Motion>', self.mouseMove)  # Mousemove Funktion
            self.polygon_coords_excl.append([x, y])  # Koordinaten für Polygon

            if len(self.polygon_coords_excl) == 2:  # Wenn zwei Punkte vorhanden: Zeichnet linien aus Klick-Koordinaten (erste Linie)
                for l in range(0, len(self.polygon_coords_excl) - 1):
                    self.lines_excl.append(canvas.create_line(self.polygon_coords_excl[l], self.polygon_coords_excl[l + 1], width=2))

            elif len(self.polygon_coords_excl) > 2:  # wie if, nur das alte Linien gelöscht werden (zweite Linie)
                del_templines()
                for l in range(0, len(self.polygon_coords_excl) - 1):
                    self.lines_excl.append(canvas.create_line(self.polygon_coords_excl[l], self.polygon_coords_excl[l + 1], width=2))
                if len(self.polygon_coords_excl) > 2:  # Falls mehr als zwei Punkte ausgewählt wurden (Willkürlich als minimale Polygongröße gewählt)
                    if abs(self.polygon_coords_excl[0][0] - x) < catch_range and abs(self.polygon_coords_excl[0][1] - y) < catch_range:  # Wenn neuer punkt nah genug an altem ist wird polygon geshclossen
                        self.polygon_excl.append(canvas.create_polygon(self.polygon_coords_excl, outline='black', fill='red', stipple="gray25", width=2)) #Erstellt liste mit Polygonen
                        del_templines()
                        self.birthmarks.append(self.polygon_coords_excl) #Polygon coordinaten in dauerhalte Liste
                        self.polygon_coords_excl = []
                        canvas.unbind('Motion', self.motion_track)
                        self.alreadyDrawed_excl = True

        def del_templines(): #Löscht temporäre Linien des Polygons
            for line in self.lines_excl:
                canvas.delete(line)

        def delpolmouse(event): #Um polygon mit rechter Maustatste zu löschen
            x = event.x  # cursor x-Position
            y = event.y  # cursor y-Position
            point = Point(x, y)
            for n in range(0,len(self.birthmarks)):
                polygon = Polygon(self.birthmarks[n])
                if polygon.contains(point): #Wenn punkt in Polygon
                    del self.birthmarks[n] #Löscht eintrag aus Liste
                    canvas.delete(self.myline) #Löscht mousMove line
                    for p in self.polygon_excl:  # Löscht alle gezeichneten Polygone
                        canvas.delete(p)
                    for i in self.birthmarks: #Zeichnet Polygone neu aus birthmarks list
                        self.polygon_excl.append(canvas.create_polygon(i, outline='black', fill='red', stipple="gray25", width=2))  # Erstellt liste mit Polygonen
                    break



        self.alreadyDrawed_excl = False  # Trigger ob schon Polygon existiert, welches gelöscht werden muss
        catch_range = 10  # Radius, in dem Polygon als geschlossen erkannt wird
        if self.trigg_button == 'first': #Wenn button das erste mal geklickt wird bzw. bei allen ungeraden anzahlen
            try:
                for p in self.polygon_excl: #Löscht gezeichnete Polygone
                    canvas.delete(p)

            except:
                pass
            self.birthmarks = []  # Löscht markierte Muttermnale
            canvas.bind('<Button-1>', cut)  # Bindet linksklick an funktion
            canvas.bind('<Button-3>', delpolmouse)
            self.myline = canvas.create_line(0, 0, 0, 0)
            self.lines_excl = [] #Liste mit tempotären linien des Polygons
            self.polygon_excl = []
            self.polygon_excl.append(canvas.create_polygon([0, 0], [0, 0], [0, 0]))
            self.polygon_coords_excl = [] #Punkte des Polygons
        else: #Wenn button das zweite mal geklickt wird bzw. bei allen gerade anzahlen
            canvas.delete(self.myline) #Löscht mousmove Linie
            del_templines()
            canvas.unbind('<Button-3>')
            try:
                canvas.unbind('Motion', self.motion_track) #unbind Funktion Mousmove
            except:
                pass


    def mouseMove(self, event): #Für linien zwischen Startpunkt und aktueller zeigerposition
        canvas.delete(self.myline)
        self.myline = canvas.create_line(self.old_coords[0], self.old_coords[1], canvas.canvasx(event.x), canvas.canvasy(event.y), width=2)



class openstream:

    def __init__(self): # Öffnet Fenster für Stream der Webcam
        def del_stream_win():
            root.deiconify()  # Root sichtbar machen
            self.stream_wind.destroy()  # Stream fenster zerstören

        def trigg(val):  # Zum setzen des Wertes der globalen Variable
            if val == 'take':
                triger_local = 'take'
            elif val == 'run':
                triger_local = 'run'
            else:
                triger_local = 'cancel'
            global trigger
            trigger = triger_local

        def z_change(v):
            try:
                z_neu = self.z_def + int(v)
                self.s.execude(f'G00 Z{z_neu}')
                self.z_def=z_neu
                self.s.execude(f'G00 X{cam_offset(self.z_def)[0]} Y{cam_offset(self.z_def)[1]}')
            except:
                tkinter.messagebox.showerror('ERROR', 'Delta nicht angeschlossen')


        self.z_def=130

        self.stream_wind = Toplevel(root)  # Erstellt neues Top-Level Fenster
        self.stream_wind.protocol("WM_DELETE_WINDOW", del_stream_win)  # Bei drücken des x-Symbols

        toolbar2 = Label(self.stream_wind)  # Erstellt Toolbar
        toolbar2.pack(side=TOP, fill=X)

        defSource = 0
        self.status_bar2 = Label(self.stream_wind, text=' Videoquelle: ' + str(defSource), bd=1, relief=SUNKEN,
                                 anchor=W)  # Statusbar
        self.status_bar2.pack(side=BOTTOM, fill=X)
        self.streamQuelle(defSource)  # Startet Stream mit quelle 0

        self.stream_label = Label(self.stream_wind)
        self.stream_label.pack()
        root.withdraw()  # Root unsichtbar machen

        stream_take = Button(toolbar2, text='Bild aufnehmen', command=lambda: trigg('take'))
        stream_take.grid(row=0, column=1, padx=5, pady=1)
        stream_cancel = Button(toolbar2, text='cancel', command=lambda: trigg('cancel'))
        stream_cancel.grid(row=0, column=2, padx=5, pady=1)
        space=Label(toolbar2, width=15)
        space.grid(row=0, column=3, padx=5, pady=1)
        hight=Label(toolbar2)
        hight.grid(row=0, column=4, padx=5, pady=1)
        up = Button(hight, text='-', command=lambda: z_change('-1'))
        up.grid(row=0, column=1, padx=5, pady=1)
        z=Label(hight, text='UP/DOWN')
        z.grid(row=0, column=2, padx=5, pady=1)
        down = Button(hight, text='+', command=lambda: z_change('1'))
        down.grid(row=0, column=3, padx=5, pady=1)

        menu = Menu(self.stream_wind)  # Erstellt Menüleiste mit namen menu
        self.stream_wind.config(menu=menu)  # ...
        menu_video = Menu(menu)  # Erstellt Eintrag in Menüleiste. Erste sichtbare Ebene
        menu.add_cascade(label='Quelle', menu=menu_video)  # ...
        menu_video.add_command(label='0', command=lambda: self.streamQuelle(0))
        menu_video.add_command(label='1', command=lambda: self.streamQuelle(1))
        menu_video.add_command(label='2', command=lambda: self.streamQuelle(2))
        menu_video.add_command(label='3', command=lambda: self.streamQuelle(3))
        menu_video.add_command(label='4', command=lambda: self.streamQuelle(4))

        trigg('run')  # Trigger setzen
        self.show_frame()  # Öffnet funktion zum zeigen des Streams

    def streamQuelle(self, videosource):
        # Für webcam-Stream
        width, height = 2592, 1994
        # Positionierung der Kamera
        try:
            self.s=send_g_code.send()
            self.s.execude('G28')
            self.s.execude(f'G00 Z{self.z_def}')
            self.s.execude(f'G00 X{cam_offset(self.z_def)[0]} Y{cam_offset(self.z_def)[1]}')
            #s.serClose()
        except:
            print("Kamera konnte nicht ausgerichtet werden")

        self.cap = cv2.VideoCapture(videosource)  # Quelle für kamera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.status_bar2.destroy()
        self.status_bar2 = Label(self.stream_wind, text=' Videoquelle: ' + str(videosource), bd=1, relief=SUNKEN,
                                 anchor=W)  # Statusbar
        self.status_bar2.pack(side=BOTTOM, fill=X)

    def show_frame(self):  # Öffnet Fensetr mit Stream der Webcam
        ret, frame = self.cap.read()
        global trigger
        if ret & bool(trigger == 'run'):  # Bei trigger=run: Stream anzeigen
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            cv2image, _ = to1920x1080(cv2image, 1)
            cv2image, _ = img_change_size(cv2image, 1)  # Größe anpassen
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.stream_label.imgtk = imgtk
            self.stream_label.configure(image=imgtk)
            self.stream_label.after(10, self.show_frame)

        elif trigger == 'take':  # Bei trigger=Take: Foto aufnehmen
            ret, frame = self.cap.read()
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

            r118 = 76.8 / 1944 #Wert ermittelt durch Versuche
            r = r118 * (self.z_def / 118)

            cv2image, r = to1920x1080(cv2image, r)

            #mtx, dist=Camera_Calibration.load_coefficients()
            #cv2image = Camera_Calibration.undistorted(cv2image, mtx, dist) # Kamera Offsets ermittelt mit Schachbrettmuster

            cv2image = rotate_image(cv2image, 1.2)  # Bild drehen

            show_img(cv2image, ratio=r)  # Aufgenommenes Bild in Hauptfensetr anzeigen.
            root.deiconify()  # Root sichtbar machen
            self.stream_wind.destroy()  # Streamfenster zerstören

        else:  # bei trigger=cancel
            root.deiconify()  # root sichtbar machen
            self.stream_wind.destroy()  # Streamfenster zwerstören



def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1])/2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    output_size=image.shape[1::-1] #(width,height)
    result = cv2.warpAffine(image, rot_mat, output_size, flags=cv2.WARP_INVERSE_MAP,  borderValue=[255,255,255])
    return result

def cam_offset(current_position):
    camera_offset_x = 0.0148 * current_position + 2.7249 - 0.2
    camera_offset_y = -0.0053 * current_position + 12.143 + 0.2
    #camera_offset_x =0.013 * current_position + 2.7571 - 0.1
    #camera_offset_y = -0.0255 * current_position + 13.224 + 3.8
    return [camera_offset_x, camera_offset_y]


def quit_dialog(): #Dialog zum Beenden
    ok_quit=tkinter.messagebox.askokcancel('Beeden?', 'Wollen Sie das Programm wirklich beenden?' )
    if ok_quit:
        root.destroy()


def open_file():
    try:
        file = tkinter.filedialog.askopenfilename()  # öffnet file dialog
        image = cv2.imread(file)  # Öffnet Bild.
        cv2image = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)  # Für Farbkorrektur
        show_img(cv2image)  # Funktion um Bild an zu zeigen
    except:
        tkinter.messagebox.showerror('ERROR', 'Bild konnte nicht geöffnet werden! \nEvtl. befinden sich Sonderzeichen im Dateipfad')



def img_change_size(cv2image, ratio):  # Größe des Bildes anpassen
    #height_max = 720  # Maximalhöhe
    #width_max = 1280  # Maximalbreite
    size = cv2image.shape
    h=size[0]
    w= size[1]
    scale_factor_w = width_max / w
    scale_factor_h = height_max / h

    if h<height_max & w<width_max: #Wenn bild in höhe und breite kleiner als maximum
        if scale_factor_h < scale_factor_w:
            scale_factor = scale_factor_h
        else:
            scale_factor = scale_factor_w
    else:
        if scale_factor_h < scale_factor_w:
            scale_factor = scale_factor_h
        else:
            scale_factor=scale_factor_w

    img = cv2.resize(cv2image, (0, 0), fx=scale_factor, fy=scale_factor)

    ratio=ratio/scale_factor #Skalierung anpassen
    return img, ratio


def to1920x1080(img, ratio):
    h, w, _ = img.shape
    scale_factor_w = 1920 / w
    scale_factor_h = 1080 / h

    if h < 1080 & w < 1920:  # Wenn bild in höhe und breite kleiner als maximum
        if scale_factor_h < scale_factor_w:
            scale_factor = scale_factor_w
        else:
            scale_factor = scale_factor_h
    else:
        if scale_factor_h < scale_factor_w:
            scale_factor = scale_factor_w
        else:
            scale_factor = scale_factor_h
    ratio = ratio / scale_factor

    img = cv2.resize(img, (0, 0), fx=scale_factor, fy=scale_factor)

    h, w, _ = img.shape

    if h-1080 > w-1920:
        c=round((h-1080)/2)
        img=img[c:1080+c, :]
    elif w-1920 > h-1080:
        c=round((w-1920)/2)
        img = img[:, c:1920 + c]

    return img, ratio


def BildMaskieren(cv2image, color, ratio, include, exclude):  # Funktion um Bild an zu zeigen
    print('Farbe: ', color)
    print('Skalierung ', ratio)
    image=cv2.cvtColor(cv2image, cv2.COLOR_RGBA2BGR) # Bild wieder in cv2 standard Farbraum
    mask_include = np.zeros(image.shape, dtype=np.uint8)  # Leere Maske erstellen
    mask_exclude = np.zeros(image.shape, dtype=np.uint8)  # Leere Maske erstellen

    tattoo = np.array([include], dtype=np.int32)  # Numpy array mit Koordinaten
    cv2.fillPoly(mask_include, tattoo, [255, 255, 255])  # Polygon
    mask_include = 255 - mask_include  # Maske Invertieren
    root.withdraw()

    for e in exclude: #Nötig da listen für np array sonst gleiche länge haben müssten
        birthmarks = np.array([e], dtype=np.int32)  # Numpy array mit Koordinaten
        cv2.fillPoly(mask_exclude, birthmarks, [255, 255, 255])  # Polygone



    # apply the mask
    masked_image = cv2.bitwise_or(image, mask_include)
    masked_image = cv2.bitwise_or(masked_image, mask_exclude)
    masked_image=rotate_image(masked_image, 0.5) #zum Rotieren des Bildes
    #cv2.imwrite('pathfinder_testbild.png', masked_image)
    #print(color, ratio)
    pathfinder_xi.pathfinder( masked_image, color, ratio,root)



root=Tk(className="delta")
root.protocol("WM_DELETE_WINDOW", quit_dialog)
l=Label(root) #Label um buttons über canvas zu plazieren
l.pack()
height_max = int(root.winfo_screenheight()*0.8) # Maximalhöhe
width_max = int(root.winfo_screenwidth()*0.9)  # Maximalbreite
global toolbar
toolbar = Label(l)  # Erstellt leere Toolbar
toolbar.pack(side=TOP, fill=X)
canvas = Canvas(l, width=width_max, height=height_max)  # Erstellt leeres Canvas mit namen canvas für ganze klasse
canvas.pack(side=BOTTOM)

# ****Main Menu als Dropdown***
menu = Menu(root)  # Erstellt Menüleiste mit namen Menü
root.config(menu=menu)  # ...
menu_datei = Menu(menu)  # Erstellt Eintrag in Menüleiste. Erste sichtbare Ebene
menu.add_cascade(label='Datei', menu=menu_datei)  # ...
menu_datei.add_command(label='Bild aus Galerie', command=open_file)  # Eintag in Menüleiste 'Date'
menu_datei.add_command(label='Bild aufnehmen', command=lambda: openstream())
menu_datei.add_separator()  # Seperator
menu_datei.add_command(label='Beenden', command=quit_dialog)
menu_hilfe = Menu(menu)  # Erstellt weiteren Eintrag in Menüleiste. Erste sichtbare Ebene
menu.add_cascade(label='Hilfe', menu=menu_hilfe)  # ...
menu_hilfe.add_command(label='Über', command=lambda: tkinter.messagebox.showinfo('Über', 'Dies ist ein Projekt der Delta-Boyz'))  # Eintag in Menüleiste 'Hilfe'

# ****Status Bar unten im Fenster***
status_bar = Label(root, text='Bitte ein Bild auswählen oder aufnehmen', bd=1, relief=SUNKEN, anchor=W)
status_bar.pack(side=BOTTOM, fill=X)


#show_img(cv2.imread('messi5.jpg')) #Bei start Bild auswählen. Für entwicklungszwecke
root.mainloop()