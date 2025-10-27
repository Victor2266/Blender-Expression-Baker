# Blender-Expression-Baker
Save a rest pose, then use any combination of bones + shapekeys to make an expression, then press a button to bake changes to your mesh as new shapekey

# Guide
1. In the 3D Viewport, press N to open the sidebar.
You will see a new tab called "Expression Baker". Click on it.
2. Select your character's main mesh.
Ensure your character is in a perfect neutral/rest pose. Click "Capture Rest Pose".
You can capture rest poses for multiple meshes at once.
3. Now, use your armature bones and any existing shape key sliders to create the desired expression (e.g., "Happy").
Once you are satisfied with the expression, click "Create Expression Shape Key".
A dialog will pop up asking you to name the new shape key. Type in "Happy" and click OK.
It will compare the rest pose to the current pose and generate a new shape key based on the differences.

Works instantly, has minimal memory impact, does not save rest pose information on closing of Blender.

<img width="333" height="100" alt="image" src="https://github.com/user-attachments/assets/6df3c206-e102-4e51-a877-0a22c8bc1e7d" />
<img width="331" height="115" alt="image" src="https://github.com/user-attachments/assets/f505b362-4a21-427d-ad6b-0b04a94b3927" />
<img width="312" height="98" alt="image" src="https://github.com/user-attachments/assets/c59b7b0e-ecd9-409f-be8d-6b9c96f7094d" />
