#!/usr/bin/env python3
import sys
import time
import turtle
from tkinter import *
#from functools import partial
from operator import itemgetter
import threading
import send_g_code
import tkinter.messagebox

import cv2
import numpy as np

def pathfinder( image, bg_color, SCALE_FACTOR,root):
    #image=cv2.imread('tattooMASKED.png',0)
    image=cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(image, bg_color, SCALE_FACTOR)
    ENLARGEMENT = 0.5
    SEARCH_RADIUS = 100

    current_position = 80

    #SCALE_FACTOR = 3

    def callback(x):
        pass


    def calculate_mask(image, limit):
        return cv2.inRange(
            image, np.array([limit]), np.array([256])
        )


    def update_display(image, limit):


        white_mask = calculate_mask(image, limit)
        #white = cv2.bitwise_and(image, image, mask=white_mask)

        vis = np.concatenate((image, white_mask), axis=1)
        cv2.imshow('Anzeige: ESC druecken um zu beenden', vis)
        cv2.imwrite('whitmaskimg.png', white_mask)


    def get_coordinates(image, limit):
        mask = np.flipud(calculate_mask(image, limit))
        ys, xs = np.nonzero(mask == 0)
        return list(zip(xs, ys))


    def find_neigbors(pixels_coordinates):
        coordinates_to_neighbors = {
            coordinates: [] for coordinates in pixels_coordinates
        }
        for x, y in pixels_coordinates:
            coordinates_to_neighbors[x, y] = [
                potential_neighbor
                for potential_neighbor in [(x + 1, y), (x - 1, y),(x - 2, y), (x, y + 1)]
                if potential_neighbor in coordinates_to_neighbors
            ]
        return coordinates_to_neighbors


    def get_lowest_left_point(pixels_coordinates):
        return min(pixels_coordinates, key=itemgetter(1, 0))


    def get_next_point(path, pixels_coordinates):
        if path:
            x, y = path[-1][-1]
            for search_radius_counter in range(1, SEARCH_RADIUS + 1):
                circle_around_point = []
                for j in range(-search_radius_counter, search_radius_counter + 1):
                    circle_around_point.append((x + j, y - search_radius_counter))
                    circle_around_point.append((x + j, y + search_radius_counter))

                for j in range(-search_radius_counter + 1, search_radius_counter):
                    circle_around_point.append((x - search_radius_counter, y + j))
                    circle_around_point.append((x + search_radius_counter, y + j))
                #
                # Sortieren nach: Direkt zuerst, diagonal anschließend.
                #
                circle_around_point.sort(
                    key=lambda point: x == point[0] or y == point[1]
                )
                for next_point in circle_around_point:
                    if next_point in pixels_coordinates:
                        return next_point

        return get_lowest_left_point(pixels_coordinates)


    def search_for_neighbor(neighbors, coordinates_to_neighbors):
        for neighbor in neighbors:
            if neighbor in coordinates_to_neighbors:
                return neighbor
        return None


    def find_path(pixels_coordinates):
        start = time.perf_counter()
        coordinates_to_neighbors = find_neigbors(pixels_coordinates)
        path = list()
        while coordinates_to_neighbors:
            point = get_next_point(path, coordinates_to_neighbors)
            neighbors = coordinates_to_neighbors.pop(point)
            path_segment = [point]
            while True:
                point = search_for_neighbor(neighbors, coordinates_to_neighbors)
                if point is None:
                    break
                neighbors = coordinates_to_neighbors.pop(point)
                path_segment.append(point)

            path.append(path_segment)

        finish = time.perf_counter()
        print(f"abgeschlossen in {finish - start:.2f} Sekunden")

        return path

    def turtle_simulation(path, width, height, t):
        offset_x = width * ENLARGEMENT / 2
        offset_y = height * ENLARGEMENT / 2
        for segment in path:
            t.up()
            for x, y in segment:
                t.goto(
                    x * ENLARGEMENT - offset_x, y * ENLARGEMENT - offset_y,
                )
                t.down()


    def run_simulation(path, enlargemnet, width, height):
        def quit_f():
            ok_quit = tkinter.messagebox.askokcancel('Abbruch?', 'Wollen Sie das Senden des G_CODES wirklich abbrechen?')
            if ok_quit:
                global trigger_laser
                trigger_laser=False
                root.deiconify()  # root sichtbar machen
                root2.destroy()

        write_g_code(path)

        root2 = Toplevel(root)

        toolbar3 = Label(root2)
        toolbar3.pack(side=TOP, fill=X)
        ImagesLB=Label(root2)
        ImagesLB.pack()

        image_left = PhotoImage(file="Hintergrund_turtle.png")
        Label(ImagesLB,image=image_left).grid(row=0, column=0)

        ccanvas = Canvas(ImagesLB, width=width * enlargemnet, height=height * enlargemnet)
        turtle_screen = turtle.TurtleScreen(ccanvas)
        turtle_screen.bgpic("Hintergrund_turtle.png")
        ccanvas.grid(row=0, column=1)

        t = turtle.RawTurtle(turtle_screen)
        t.color("red")
        threading.Thread(
            target=turtle_simulation, args=[path, width, height, t], daemon=True
        ).start()

        global continue_button
        continue_button = Button(toolbar3, text="Starten", command=lambda: threading.Thread(target=send_g_code_f, daemon=True).start())
        continue_button.grid(row=0, column=0, padx=5, pady=1)
        exit_button = Button(toolbar3, text="Abbrechen", command=quit_f )
        exit_button.grid(row=0, column=1,padx=5, pady=1)

        root2.protocol("WM_DELETE_WINDOW", quit_f)  # Bei drücken des x-Symbols

        root2.mainloop()

    def caluclate_offsets(current_position):
        #camera_offset_x = 0.0201*current_position+2.3737
        #camera_offset_y = -0.0275*current_position+13.293
        return (width * SCALE_FACTOR * 0.5, height * SCALE_FACTOR * 0.5 ) #-0.5 -0.05


    def write_g_code(path):
        x_offset, y_offset = caluclate_offsets(current_position)
        with open("g_code.txt", "w", encoding="ascii") as g_code_file:
            #x_offset=width*SCALE_FACTOR*0.5 + 4
            #y_offset = height * SCALE_FACTOR * 0.5 + 11
            g_code_file.write("M665 L241 R143 H210 B100 X0 Y0 Z0 \n")
            g_code_file.write("G28 \n")
            g_code_file.write("G00 Z46\n")
            #g_code_file.write(f"G00 X {x_null} Y {y_null}\nG92 X0 Y0\n")
            #g_code_file.write("G55 X-50 Y-50\n")
            for segment in map(iter, path):
                x, y = next(segment)
                outer_smoothing_value_x = 0 #x*0.1
                outer_smoothing_value_y = 0 #y*0.1
                g_code_file.write(f"G00 X{(x + outer_smoothing_value_x) * SCALE_FACTOR - x_offset:10.2f}"
                                  f" Y{(y + outer_smoothing_value_y) * SCALE_FACTOR-y_offset:10.2f}"
                                  f" F1000 \nM106 \n")
                g_code_file.writelines(f"G01 X{(x + outer_smoothing_value_x)*SCALE_FACTOR-x_offset :10.2f}"
                                       f" Y{(y +  outer_smoothing_value_y)*SCALE_FACTOR-y_offset:10.2f}"
                                       f" F200 \n" for x, y in segment)
                g_code_file.write("M107 \n")
            g_code_file.write("G00 Z100 F1000\n")
            g_code_file.write("G00 X0 Y0 F1000\n")

    def send_g_code_f():
        global continue_button
        continue_button.config(state='disabled')
        s=send_g_code.send()
        state=s.txt()
        if state:
            tkinter.messagebox.showinfo('FINISHED', 'G-CODE erfolgreich ausgeführt')
        else:
            tkinter.messagebox.showerror('ERROR','G-CODE konnte nicht erfolgreich ausgeführt werden')



    #def main():
    np.set_printoptions(threshold=sys.maxsize)
    #
    # Pixel-Detektion.
    #
    #image = cv2.imread("test4.png", 0)

    display_image = cv2.resize(image, (0, 0), fx=ENLARGEMENT, fy=ENLARGEMENT)
    cv2.imwrite("Hintergrund_turtle.png", display_image)

    #update_display(display_image, 0)

    cv2.namedWindow("Anzeige: ESC druecken um zu beenden")
    cv2.createTrackbar("Trackbar", "Anzeige: ESC druecken um zu beenden", 0, 256, callback)

    cv2.setTrackbarPos("Trackbar", "Anzeige: ESC druecken um zu beenden", int((bg_color[0]+bg_color[1]+bg_color[2])/3)-15)           #set default value

    while True:
        limit = cv2.getTrackbarPos("Trackbar", "Anzeige: ESC druecken um zu beenden")

        update_display(display_image, limit)

        key = cv2.waitKey(1)

        if key == 27:
            cv2.destroyAllWindows()
            break

    #
    # Ab hier Pfad bestimmen.
    #
    path = find_path(get_coordinates(image, limit))
    print(path)
    #
    # Ab hier Simulation.
    #
    global trigger_laser
    trigger_laser=True
    height, width = image.shape[:2]
    run_simulation(
        path, ENLARGEMENT, width, height
    )
    print("erreicht")
    #
    # G Code erstellen
    #



if __name__ == "__main__":
    root=Tk()
    pathfinder(cv2.imread('pathfinder_testbild.png'), [236, 214, 199], 0.10853548048545139, root)
    root.mainloop()
#pathfinder(cv2.imread('test001.jpg'), [100,100,100], 111.23423423)