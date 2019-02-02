# MultiClass Annotation Tool
The GUI application will allow to view the images and annotate them according to corresponding class. 
For every image, annotation consist of n (number of classes) numbers either 0 or 1 depending upon class exists in image or not. 

A sample images folder is provided in the repository. You can try on them first to see how the application works.

You can modify Number of classes depending upon your dataset and the way you want to train.

**Clone the Repository**

Now clone the repository to your machine. Go to your terminal and the type:
```
git clone https://github.com/nilbarde/ImageViewer
```

Paste the image files in the images folder.

Install the dependencies required for the application to run

```
sudo pip install -r requirements.txt
```

or install them separately

```
sudo pip install cython
sudo pip install kivy
sudo pip install pygame
```

Instructions for Usage
1. Application loads Image list from folder images. <br>

2. Application annotates Image using DefaultDict defined in Initializatin of Class. <br>

3. You can modify annotation using defined Keyboard shortcuts (which can be modified according to usage) or clicking on corresponding button or checkbox.<br>

4. If image is not good or not usable for training use wrong button to delete image.<br>

5. When annotation gets complete click on correct button (or keyboard shortcut). Images gets transferred to final_images folder and Annotation json file is created with name same as image name and appropriate extension.<br>

