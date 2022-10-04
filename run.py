import os

os.system("cd stablediffusion-infinity/PyPatchMatch && make clean && make")
os.system("cd stablediffusion-infinity && python app.py")