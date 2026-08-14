# Open-source software for multi-modal imaging using the XIM framework.

## Getting Started
You need (in general):
- Micro Manager 2.0 (latest nightly-build) should generally work
- Drivers for hardware e.g., stage, camera etc. that are MM 2.0 compatible, refer to: https://micro-manager.org/Device_Support for complete list.
- Arduino (ver?) to trigger the MS acquisition

## Application Example: Imaging & wellpate reading in CL3
<img width="1280" height="960" alt="photo_6046450931089477667_y" src="https://github.com/user-attachments/assets/4b91efb9-0499-40c0-9bae-77b5ce04cd42" />

### Before you start the run
Start jupyter notebook (from the quick start bar or search jupyter notebook in the search bar), the notebook (**FIM_acq.ipynb**) that controls this XIM setup can be found on the desktop, under FIM_CL3/XIM. You will also need to **start Micro Manager first before running the notebook** (also from Desktop), the default configuration file (FIMM.cfg) should be used.

The first thing to do is to load all the dependencies and create an experiment object with predefined acquisition parameters, which controls all the hardware here, from camera to MS trigger.

<img width="2088" height="866" alt="image" src="https://github.com/user-attachments/assets/a09545dc-4bbf-49c2-8fe5-04d7db967166" />


To load you sample, open the cabinet door and unload the stage by running:

`exp.sample_unload()`

<img width="960" height="1280" alt="photo_6046450931089477668_y" src="https://github.com/user-attachments/assets/a8625998-a50a-4dfe-928d-4993b64ea309" />

This should give you access to the stage mount, press the release buttons (highlighted) and drag the closer holder bar towards you, mount the slide to be imaged (sample-side up, the 'wrong-way'!), then push back the bar to securely fix the sample:

<img width="960" height="1280" alt="photo_6046450931089477669_y" src="https://github.com/user-attachments/assets/0437bf58-7396-4755-832f-c0481130d55b" />

Once done, you can load the sample by running:

`exp.sample_load()`

### Magellan-enabled wholeslide imaging & ROI selection
After the sample is place, the next step is to determine the region-of-interest (ROI) to be imaged by MSI. To do so, we make use of micro-magellan controlled by pycro manager, which facilitates fast, widefield imaging under brightfield illumination. First, make sure that the light source is connected (see below):

<img width="960" height="1280" alt="photo_6046450931089477670_y" src="https://github.com/user-attachments/assets/7b6e8b32-1fdd-46aa-9443-498d03321896" />

To test that camera is working and the image in-focus, you can start a live acquisition on micro manager (highlighted):

<img width="511" height="216" alt="image" src="https://github.com/user-attachments/assets/bf01a0c4-c42f-45d9-b0de-a37df79d59ff" />

You can adjust the focus by turning the manual gauge on the microscope, a focused image should look like this:

example image

Start the ROI selection process by running the cell under **Magellan-based ROI exploration**:

`acq = MagellanAcquisition(magellan_explore=True)`

`acq.mark_finished()`

This will trigger a new window with the Magellan Explore function, which allows one to explore the sample plane by stitching together tiles (FOVs):

<img width="1168" height="585" alt="image" src="https://github.com/user-attachments/assets/1bae44eb-3884-4ca1-a1eb-c16383e7b7f5" />

**Left-click to select the tiles to be imaged (click again to start acquisition) and right-click cancels, middle mouse scroll to zoom in/out.** This works essentially akin to the classic 'minesweeper' game where the objective is to find the tiles with desirable features e.g., the edges of a tissue.

To draw ROI(s), go to the **'Grids and Surfaces'** tab, click 'New Surface', then draw any polygon that describes your desired ROI, for example:

<img width="303" height="255" alt="image" src="https://github.com/user-attachments/assets/21d08836-dc6f-483d-886c-6a3eb7487001" />

**You can draw as many ROIs as you want! Each will generate a different exp file and can be queued on MassLynx to e.g., image multiple tissues on the same slide automatically.**

**Note that you do not have to fill and image the whole sample.** If the objective is to select the whole sample, a good practice is to find the opposing corners of the bounding rectangle (e.g., top left to bottom right) then draw around that. Conversely, if you only want to focus on certain spatial regions on the sample, you can just select them individually.

The brightfield image is nonetheless useful for downstream analysis, such as co-registration as it retains subcellular resolution (albeit in grayscale unless in fluorescence mode). **To save the Magellan-generated image, go to the control window for Micro-Magellan explore and set the saving directory and saving name**, then simply close the acquisition window (or clicking stop acquistion, the 'red cross'). A prompt will ask to confirm 'Finish acquisition', and then the image would be automatically saved. 

### Setting up the experiment file(s)
After ROI(s) have been selected, run the next cell under '**Calculate start position & XY parameters for exp file(s) according to selected ROI(s)**':

<img width="894" height="640" alt="image" src="https://github.com/user-attachments/assets/e181e4a2-e6dc-4d64-bed4-343927230ebc" />

This will auto-calculate & generate the ROI(s) that will be imaged based on the coordinate system of the imaging stage.

Then run the next cell under '**Generate exp file(s) to start run**':

<img width="892" height="428" alt="image" src="https://github.com/user-attachments/assets/02c0aba3-1c80-493d-9870-7ae35771e7be" />

You can set the experiment name (here _'test'_), and the x & y pixel resolutions (here _25um_), a different exp file is generated for each ROI drawn in Magellan. The generated exp files will be under the same root directory as the notebook.

### Starting the run
Before starting the run, follow the checklist:

1. Turn the MS on and calibrate (with sodium formate).
2. Set solvent matrix (IPA) flow to 0.1 ul/min.
3. Turn the REIMS source on.
4. Check that shutter is closed.
5. Turn the Laser on.
6. Load the .exp file(s) in MassLynx and start run.

Note 1: It is easier to see the shutter from side of the cabinet.

Note 2: The laser control software is in the same root folder as the notebook, simply called IvyGUI. The only thing to control is the rep. rate which is by default set to 170 Hz (the maximum). Anything lower will start to decrease the laser power more or less linearly, so there is no need to tunes this in general.

  <img width="466" height="341" alt="image" src="https://github.com/user-attachments/assets/91d3a593-6828-46bc-b924-62b642076497" />












