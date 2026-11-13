# nuclear-fuelrod-handover-robot-sim

# Overview
Multi-Robot Manipulation & Digital Twin Simulation — CoppeliaSim, ROS2, Python
Designed and implemented a digital twin of a 4-robot Niryo-1 arm chain tasked with sequentially transferring a fragile payload through constrained apertures. Integrated proximity sensing with ROS2 inter-process communication to trigger autonomous pick-and-place sequences. Validated simulation against physical prototype performance.

# How it works
Robot 1 picks up the rod and presents it to Robot 2 through an aperture in the Perspex wall.
Robot 2 collects the rod, and then presents to robot 3 through an aperture.
Robot 3 collects the rod, and then presents to robot 4 through an aperture.
Robot 4 collects the rod and locates it in its final position.

The simulation uses proximity sensors, the robot arm initiates the pick-up movement when detecting the rod is in the
range.A conveyor delivers the rod to the robot.

# Link to video
https://drive.google.com/drive/folders/1hHx9hfHba7iK9sLNtkvqDfa0oNnqh7A_?usp=share_link
