# Welcome
This repository contains the scripts developed to run the Virtual River Platform, developed in the RiverCare research program (https://kbase.ncr-web.org/rivercare/projects/project-g1/), supported by the Netherlands Organization for Scientific Research (NWO) and partly funded by the Ministry of Economic Affairs under grant number P12-14 (Perspective Programme). The platform links a physical game board to digital models. Through the scripts, the physical game board is captured and turned digital and subsequently processed so that it is used as input for a hydrodynamic (Delft3D Flexible Mesh), ecological (BIOSAFE), and costs (VRCost) models. These models were linked to the platform for the Virtual River Game, a serious games on Dutch river management. The platform can be used to transfer the Virtual River Game or develop new serious games with a spatial component. The platform can be fully customized to those ends.

# Requirements
To run the full version of the software, you will need:
- Windows/Linux system
- Python 3
- Delft3D Flexible Mesh (tested version Delft3D FM Suite 2019.01 (1.5.1.41875)
- Virtual River game table
- Tygron Geodesign Platform (https://www.tygron.com/nl/, requires a license)

A test version of the software can be run without the game table. The scripts can be run with and without the Tygron Geodesign Platform. The scripts themselves determine if a game table or the Tygron Geodesign Platform is connected, there is no need to make adjustments in the scripts to that end.

If you wish to construct the Virtual River game table, please contact the authors (see below). We will happily supply you with the table's drawings.

# Install
To install the Virtual River Platform, please follow these steps:
- Download the Github
- Create a new Python environment using the requirements.txt or environment.yml files
- Install Delft3D FM
- Add Delft3D to system variables
- Run the Virtual River through the VirtualRiverGUI script
(- Install Tygron Geodesign Platform)

To run the full version of the software, you may need to do additional tweaking. For example, if your system is connected to the game table and has another webcam, check which webcam value should be used in the webcamControl script. If you are using the game table, you may also need to tweak some variables in the init_screens() function of the visualizer script to move the projection to the right position. You will also need to add the Delft3D FM model to your system variables so that it is found when initiated.

If you are using Tygron, create two text files and name these 'username' and 'password' and store these somewhere on your computer. Add your Tygron username and password in the respective file with no additional text. Update the references to these files in the tygron_login() function in the VirtualRiverGUI script.

# Authors
The authors of the Virtual River are Robert-Jan den Haan (https://people.utwente.nl/r.j.denhaan) and Fedor Baart (https://www.deltares.nl/nl/experts/fedor-baart-2/). 

The Virtual River was inspired and based on the SandBox-FM by Deltares (https://www.deltares.nl/en/software/sandbox/).

# Contributing
If you wish to use or expand on the platform, do not hesitate to contact us! Please also do not hesitate to contact us if you spot any bugs or have any suggestions or feedback.