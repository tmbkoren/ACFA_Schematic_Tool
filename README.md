# ACFA Schematic Tool

### Tested only on unencryptes US save files (e.g. PCFA pack)

Schematic file location: `PCFA\EMULATOR\dev_hdd0\home\00000001\savedata\BLUS30187ASSMBLY064\DESDOC.DAT`
Each time you import a schematic, it will create a .bak file in case the save file get corrupted.

Credits go to https://github.com/WarpZephyr/ for figuring out the schematic savefile offsets 

### To run:
1. install requirements `pip install -r requirements.txt`
2. `python ACFA_Schematic_Tool_GUI/app.py`

### To build:
`pyinstaller ACFA_Schematic_Tool_GUI/app.py --onefile --name ACFA_Schematic_Tool --add-data "ACFA_PS3_US_PARTID_TO_PARTNAME.txt;."`