# Virtual-River-prototype
Scripts to run the Virtual River game interface as developed in the RiverCare research program (https://kbase.ncr-web.org/rivercare/projects/project-g1/). The hybrid, tangible user interface that combines a physical game board with digital models is inspired and based on the SandBox-FM by Deltares (https://www.deltares.nl/en/software/sandbox/).

The scripts converts the physical board state to the digital board and runs different models. It includes a calibration and image processing script to analyze the current board state of Virtual River. It processes pictures taken of the current game board, taken from below the game board, and analyzes the game pieces that are placed in each gridcell. Subsequently creates an elevation model of the board based interpolation, sets the land use of each cell and runs the hydrodynamic model (Delft3D-FM) with the elevation model and roughness coefficients in relation to the land uses.

Run Virtual River through VirtualRiverGUI.py

TODO: rest of readme.