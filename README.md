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

