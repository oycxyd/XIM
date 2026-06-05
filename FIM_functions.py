# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 15:29:16 2023
@author: Administrator
'All-in-one' script for FOG's MSI platform

Intended use:
    # initialise controller
    exp = Exp()
   
    # prepare .exp file and controller for 10um^2 pixel, 1mm^2 scan area
    exp.prepare('myfilename',10,10,1,1)
   
    # load the .exp and begin acquisition in MassLynx
   
    # Start the raster scan
    exp.do_full_raster()
   
    # to not break windows, close the serial ports if required
    exp.close()
"""
import sys
import os
import numpy as np
from scipy.signal import convolve2d
import ctypes
import ctypes.util
import time
import datetime
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd
import socket
import tqdm

# arduino
import serial

# MM Core
from pycromanager import Core

## Z axis MFACC
#from MFACC_minimal import MFACC


def _init_arduino(com_port="COM9"):
    arduino = serial.Serial(com_port,9600,timeout = 0.1) # timeout = 0.1
    # trigger signal is arduino.write(b'2')
    return arduino

#def _init_Z_stage(com_port="COM6"):
#    zstage = MFACC(port=com_port)
#    print("MFACC Z stage may need homing, check it moves and has green light")
#    return zstage

def _init_pycro_core():
    core = Core()
    return core

def make_exp_file(fn,px,py, dx, dy, velocity):
    readable = f"""
pixel size ({px},{py})um^2,
image size ~({dx},{dy})mm^2
velocity {velocity}um/s
This means a time per line of ~{dx*1e3/velocity}s (plus flyback), and {int(dy*1e3/py)} or {int(dy*1e3/py)+1} lines.
"""
    print(readable)
   
    # get todays date and generate .exp filename prefix
    today = datetime.date.today()
    prefix = today.strftime('%Y_%m_%d')
    # folder where .exp will be saved
    # acq_path = 'C:/MassLynx/Default.pro/Acqudb'
    acq_path = 'C:/Users/olive/Dropbox/FIM/Scripts'
  
    # copy data from template file
    # with open('C:/MassLynx/Default.pro/Acqudb/template_negative_sensitive_10Hz.exp', 'r') as template:
    with open('C:/Users/olive/Dropbox/FIM/Scripts/template_negative_sensitive_10Hz.exp', 'r') as template:
        coretxt = template.readlines()
    # generate new experiment file
    new_exp_fn = f'{acq_path}/{prefix}_{fn}.exp'
    with open(new_exp_fn,'w') as exp:
        # copy in the template contents
        exp.writelines(coretxt)
        # append custom Desi commands
        exp.writelines(f"""
                       
DesiXStart,0.0
DesiYStart,0.0
DesiXLength,{dx}
DesiXStep,{px/1e3}
DesiXRate,100
DesiYLength,{dy+0.5*py/1e3}
DesiYStep,{py/1e3}
DesiSlot,A
""")
    print(f"""New .exp file created for use in MassLynx (testing still required!):
{new_exp_fn}""")

    return new_exp_fn,px,py,dx,dy,velocity

class Exp():
    def __init__(self, init=True):
        """Initialise the shutter/arduino(MS trigger)/Zaber stage XY/MFACC stage Z.
        """
        if init:
            self.mstrig = _init_arduino()
            self.core = _init_pycro_core()
#            self.zstage = _init_Z_stage()
           
            # define convinience dictionary of units
#            self.unit_args = {'unit':Units.LENGTH_MILLIMETRES, # for lengths
#                              'velocity_unit':Units.VELOCITY_MICROMETRES_PER_SECOND}
   
    def optimise_focus(self):
        print("""You have to do this by hand. To help, you can use the following alongisde a dummy MS file.    
                Exp.toggle_shutter()
                Exp.move_z(+/- distance in mm)
              """)
   
    def shutteredline(self, distance, velocity, gap):
        self.toggle_shutter()
        self.a2.move_relative(self.distance,
                              wait_until_idle=False,
                              velocity=self.velocity,
                              **self.unit_args)
        self.toggle_shutter()
        self.a1.move_relative(self.gap,
                              **self.unit_args)
        self.a2.move_relative(-self.distance,
                              **self.unit_args)
             
    def move_new_sample(self):
        print('TODO')
   
    def move_center_sample(self):
        print('TODO')
           
    def prepare(self, exp_name,px,py,dx,dy,velocity):
        """Define experimental variables here.
        (px,py), pixel dimensions in um
        (dx,dy), scan area in mm
        velocity, X scan speed in um/s (work this out for yourself,currently assuming 10Hz acquisition)
        """
        # do some testing here possibly
        exp_fn = make_exp_file(exp_name,px, py, dx, dy, velocity)
        self.px = px
        self.py = py
        self.dx = dx*1000
        x_current = self.core.get_x_position()
        self.dy = dy*1000
        self.velocity = velocity/1000
        return exp_fn
   
    def toggle_shutter(self):
        self.core.set_property("SC10","SC10 Command:", 'ens')
    def trigger_ms(self):
        self.mstrig.write(b'2')
#    def move_z(self, distance_mm):
#        self.zstage.move(distance_mm)

    def do_full_raster(self):
        self.origin = [self.core.get_x_position(),self.core.get_y_position()]
        lines = int(self.dy/(self.py)) + 1 # define number of lines
        comp = 0
        print(f'Start time: {datetime.datetime.now()}')
        while comp < lines:
            self._print_status(lines,comp)
            self.do_one_raster()
            comp += 1
        self._print_status(lines, comp) # print the 'finished' status
       
    def _print_status(self,lines,complete):
        sys.stdout.write("\r")
        sys.stdout.write(f"{complete}/{lines} done ({int(complete/lines*100)}%)")
       
    def do_one_raster(self,margin=1.05):
        # TODO: experimentally validate this, adjust timing/sleeps/stage directions as required
        # maths of triggering
        # freq = self.velocity/self.px # um/s / um
        # dt_shut = 1.0/freq
        # dt_adj = 5e-5
        # N_trig = int(self.dx/(self.px/1e3))
        # start move in x
        self.core.set_property("XYStage","Speed Y [mm/s]", float(self.velocity))
        self.core.set_xy_position(self.core.get_x_position(),self.core.get_y_position()+self.dx)

        self.toggle_shutter()

        # # do triggering
        # n_done = 0
        # time.sleep(0.001) # do we need to be careful at begining/near margin?
        # while n_done < N_trig:
        #     self.trigger_ms()
        #     time.sleep(dt_shut-dt_adj)
        #     n_done += 1
       
        time.sleep(0.25)     # fine tune parameter
        self.trigger_ms()
       
        # wait for line to finish
        while self.core.device_busy('XYStage'):
            # print('stage moving')
            continue
        self.toggle_shutter()
        time.sleep(0.03) # approx shutter responce time
        # do dy step. No velocity here, so default max is used

        # flyback
        self.core.set_property("XYStage","Speed Y [mm/s]", 10)
        print('flyback')
        self.core.set_xy_position(self.core.get_x_position(),self.core.get_y_position()-self.dx)
        time.sleep(0.25)
        while self.core.device_busy('XYStage'):
            # print('stage moving')
            continue
           
        self.core.set_xy_position(self.core.get_x_position()+self.py,self.core.get_y_position())
        while self.core.device_busy('XYStage'):
            # print('stage moving')
            continue
       
       
    # def sample_unload(self):
    #     self.zstage = _init_Z_stage()
    #     current_a1_position = self.a1.get_position()
    #     distance_mm = float(130) - current_a1_position/10^7
    #     self.a1.move_relative(distance_mm,
    #                           **self.unit_args)
   
    # def sample_load(self):
    #     self.a1.move_relative(50,
    #                           wait_until_idle=True,
    #                           velocity = 250,
    #                           velocity_unit = 'um/s',
    #                           **self.unit_args)
   
   
    def single_raster(self, velocity_um_s, length_x, step_y):
        self.velocity= velocity_um_s
        margin=1.0
        self.py = step_y
        self.dx = length_x
        self.do_one_raster(margin)
       
       
    def close(self):
#        self._stage_c.close() # close stage connection
        self.mstrig.close() # close arduino connection
   
#        self.zstage.close()
        # thorlab shutter connection doesn't need to be closed
    def unload(self):
        self.a1.position = 70
        self.a2.position = 100
       
    def load(self):
        self.a1.position = 70
        self.a2.position = 60

    def smallrasterspeedy(exp, vel=100, dist=0.5):
        exp.toggle_shutter()
        time.sleep(0.1)
        exp.a1.move_relative(dist,wait_until_idle=True,velocity=vel,**exp.unit_args)
        exp.toggle_shutter()
        time.sleep(0.1)
        exp.a2.move_relative(0.02,wait_until_idle=False,velocity=vel,**exp.unit_args)
        exp.a1.move_relative(-dist,wait_until_idle=False,velocity=1000,**exp.unit_args)


    def acquire_tile(self, pixel = 0.56, overlap=10, acq_area_x = 10, acq_area_y = 10, x_flip = 1, y_flip = 1):
        self.a1.set_velocity_parameters(0,10,10)
        self.a2.set_velocity_parameters(0,10,10)
        tile_width = self.core.get_image_width()
        tile_width = tile_width*pixel/1000
        tile_height = self.core.get_image_height()
        tile_height = tile_height*pixel/1000

        ## Gridding
        grid_dims = [int(np.ceil(acq_area_x/tile_width)),int(np.ceil(acq_area_y/tile_height))]

        grid_X, grid_Y = np.meshgrid(np.arange(0,grid_dims[0]), np.arange(0,grid_dims[1]), indexing='xy')
        locs = []
        x_start = self.a1.position+np.floor(grid_dims[0]/2)*tile_width
        y_start = self.a2.position-np.floor(grid_dims[1]/2)*tile_height

        for n in range(grid_dims[0]):
            for m in range(grid_dims[1]):
                # grid.append([n,m])
                locs.append([x_start+x_flip*tile_width*n, y_start+y_flip*tile_height*m])

        start_time = time.time()
        images = []
        exposure = self.core.get_exposure()
        for n,pos in enumerate(locs):
            self.a1.position = pos[0]
            self.a2.position = pos[1]
            while self.a1.is_in_motion:
                time.sleep(exposure*1e-3)
            while self.a2.is_in_motion:
                time.sleep(exposure*1e-3)
            self.core.snap_image()
            tagged_image = self.core.get_tagged_image()
            pixels = np.reshape(tagged_image.pix,
                                newshape=[tagged_image.tags['Height'], tagged_image.tags['Width'],4])
            images.append(pixels[:,:,1])

        end_time = time.time()

        elapsed_time = end_time - start_time
        print('each tile will be '+str(np.round(tile_width,decimals=2))+' mm wide & '+str(np.round(tile_height,decimals=2))+' mm tall.')
        print(f"Acquisition finished in {elapsed_time:.2f} seconds")
        return images, locs, grid_X, grid_Y

    def stitch_tiles (self,images, scale_factor = 4, overlap=10, grid_dims = [0,0], save = True):
        perc_overlap_x = overlap
        perc_overlap_y = overlap

        x_overlap = np.round(self.core.get_image_width()/scale_factor*perc_overlap_x/100+1)
        y_overlap = np.round(self.core.get_image_height()/scale_factor*perc_overlap_y/100+1)

    
        x_size = self.core.get_image_width()/scale_factor-x_overlap+1
        y_size = self.core.get_image_height()/scale_factor-y_overlap+1
        W = np.ones((int(x_size),int(y_size)))
        K = np.ones((int(x_overlap),int(y_overlap)))/(grid_dims[0]*grid_dims[1])
        K[0,:] = 0;K[:,0] = 0;

        W1 = convolve2d(W,K, mode='full')
        # image1 = Image.fromarray(images[0])
        ImR = np.zeros((W1.shape[1]*grid_dims[1],W1.shape[0]*grid_dims[0]))
        # % ImR = zeros(round((size(W1,1)-(y_overlap-1)/2))*tile_dims(2),round((size(W1,2)-(x_overlap-1)/2))*tile_dims(1));
        try:
            n = 0
            for i1 in range(grid_dims[0]):
                for i2 in range(grid_dims[1]):
                    # print(str(n))
                    image = Image.fromarray(images[n])
                    image = image.resize((int(self.core.get_image_width()/scale_factor),int(self.core.get_image_height()/scale_factor)))
                    ImR[int(y_size)*(i2):int(y_size)*(i2)+ W1.shape[1],int(x_size)*(i1):int(x_size)*(i1)+ W1.shape[0]] = ImR[int(y_size)*(i2):int(y_size)*(i2)+ W1.shape[1],int(x_size)*(i1):int(x_size)*(i1)+ W1.shape[0]] + np.transpose(W1)*(image)
                # ImR.shape
                    n = n+1
                # ImR = Image.fromarray(ImR)
            if save:
                plt.imsave('optical ROIs/whole_tissue_'+str(datetime.date.today())+'.png', ImR, cmap='gray')
            plt.imshow(ImR,cmap = 'gray')
            return ImR
        except:
            print('Error!')

    def calculate_ROI (self,xlist = [], ylist = [],x_offset = 121.984, y_offset = 193.984):
        image_width = round((np.max(ylist)-np.min(ylist)+87.552)/1000,2)
        image_height = round((np.max(xlist)-np.min(xlist)+183.296)/1000,2)
        # print(x_gind)
        # print(y_gind)
        start_pos = [np.min(xlist)-183.296/2+x_offset,np.min(ylist)-87.552/2+y_offset]
        print('the ROI starting position will be '+str(np.round(start_pos,decimals=2))+' & the size will be ')
        print(str(image_width)+ ' mm by')
        print(str(image_height)+ 'mm')
        return start_pos, image_width, image_height

    ## generate Archimedes' spirals and scan (96) wellplate
    def wellplate_read(self,a = 0.1, b = 0.25, start_pos = [], x_flip = 1, y_flip = 1, wells = 96):
        theta = np.linspace(0, 10*np.pi, 40)  # Angle range
        r = a + b * theta
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        if not start_pos:
            start_pos = [self.a1.position, self.a2.position]
        self.a1.position = start_pos[0]
        self.a2.position = start_pos[1]
        # print(start_pos)

        if wells == 96:
            grid_dims = [int(8),int(12)] #96 wellplate
        else:
            grid_dims = [int(1),int(1)] #other wellplate
        
        grid_X, grid_Y = np.meshgrid(np.arange(0,grid_dims[0]), np.arange(0,grid_dims[1]), indexing='xy')
        locs = []
        x_start = start_pos[0]
        y_start = start_pos[1]

        for n in range(grid_dims[0]):
            for m in range(grid_dims[1]):
                locs.append([x_start+x_flip*9*n, y_start+y_flip*9*m])
        locs = np.array(locs)
        locs = locs.reshape(12,8,2)
        locs[1::2] = np.flip(locs[1::2], axis=1)
        locs = locs.reshape(96,2)

        exposure = self.coreget_exposur.e()
        for n, pos in enumerate(locs):
            m = 0
            print(f"Scanning well {n+1} ...")
            self.a1.position = pos[0]
            self.a2.position = pos[1]
            while self.a1.is_in_motion:
                    time.sleep(exposure*1e-3)
            while self.a2.is_in_motion:
                time.sleep(exposure*1e-3)
            start_time = time.time()

            # self.toggle_shutter()
            time.sleep(0.03) # approx shutter responce time
            
            while True:
                self.a1.position = pos[0]+round(x[m],2)
                self.a2.position = pos[1]+round(y[m],2)
                while self.a1.is_in_motion:
                    time.sleep(exposure*1e-3)
                while self.a2.is_in_motion:
                    time.sleep(exposure*1e-3)
                m = m+1
                
                if time.time() - start_time > 2:
                    print("Next well.")
                    # self.toggle_shutter()
                    time.sleep(0.03) # approx shutter responce time
                    break

        print('All done!')

    SEPARATOR = "<SEPARATOR>"
    BUFFER_SIZE = 1024 * 4 #4KB

    def send_file(self,filename, host, port):
        # get the file size
        filesize = os.path.getsize(filename)
        # create the client socket
        s = socket.socket()
        print(f"[+] Connecting to {host}:{port}")
        s.connect((host, port))
        print("[+] Connected.")

        # send the filename and filesize
        s.send(f"{filename}{SEPARATOR}{filesize}".encode())

        # start sending the file
        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    # file transmitting is done
                    break
                # we use sendall to assure transimission in 
                # busy networks
                s.sendall(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))

        # close the socket
        s.close()

if __name__=='__main__':
    exp = Exp()
    exp.prepare('MB_ctrl_30um',30,30,7.5,10,300) 