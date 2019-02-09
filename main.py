import kivy

from kivy.app import App

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView

from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.label import Label

from codecs import open as co_open
from json import dump as j_dump
from json import load as j_load

from os import listdir, remove, walk, makedirs
from os.path import dirname, exists
from shutil import copyfile, move

import cv2
import numpy as np
from functools import partial

class ImageButton(ButtonBehavior, Image):
	pass

class HomeScreen(Screen):
	def __init__(self,**kwargs):
		super(HomeScreen,self).__init__(**kwargs)

		self.JsonPath = "./TrafficLight.json"
		self.LoadImageList()
		self.DefineImageView()
		self.DefineButtonView()

		# Classes and their naming
		self.Lights = {
						0:"Red Solid",
						1:"Yellow Solid",
						2:"Green Solid",
						3:"Green Left",
						4:"Green Straight",
						5:"Green Right"
						}
		self.NumClasses = len(self.Lights)
		# DefaultDict for by default annotation after opening image 
		self.DefaulDict = [0 for i in range(self.NumClasses)]

		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		self._keyboard.bind(on_key_down=self._on_keyboard_down)

	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_down)
		self._keyboard = None

	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		# Reading Keyboard Inputs
		if not(self.NowImage<len(self.DataList)):
			print("return")
			return
		key_no, self.pressed_key = keycode
		num_str = [str(i+1) for i in range(self.NumClasses)]

		# Shortcut Keys
		if(self.pressed_key[:6]=="numpad"):
			num = int(self.pressed_key[6]) - 1
			if(-1<num<self.NumClasses):
				self.ToggleCheckBox(num)
		elif(self.pressed_key in num_str):
			num = int(self.pressed_key) - 1
			self.ToggleCheckBox(num)
		elif(self.pressed_key=="a"):
			self.ClearSelection()
		elif(self.pressed_key=="s"):
			self.SaveImage(True)
		elif(self.pressed_key=="d"):
			self.SaveImage(False)

	def LoadImageList(self):
		self.LoadDataDir = "./images/"
		self.SaveDataDir = "./final_images/"

		# loading image list from folder and subfolders of LoadDataDir
		folders = self.get_folders(self.LoadDataDir)
		self.DataList = self.get_files(folders,".jpg")
		self.DataList.sort()

		self.NowImage = -1

	def DefineImageView(self):
		# Position of Image And Annotation
		self.DataW, self.DataH = 0.5, 0.5
		self.DataX, self.DataY = 0.3, 0.7

		self.AnnotW, self.AnnotH = 0.3, 0.1
		self.AnnotX, self.AnnotY = 0.3, 0.35

	def DefineButtonView(self):
		# Position of Buttons and List of Classes
		self.CorrectW, self.CorrectH = 0.24, 0.1
		self.CorrectX, self.CorrectY = 0.375, 0.15
		self.WrongW, self.WrongH = 0.24, 0.1
		self.WrongX, self.WrongY = 0.625, 0.15
		self.ClearW, self.ClearH = 0.24, 0.1
		self.ClearX, self.ClearY = 0.125, 0.15

		self.ListW, self.ListH = 0.24, 0.9
		self.ListX, self.ListY = 0.875, 0.5

	def on_pre_enter(self):
		self.OpenNextImage()

	def cust_pre_enter(self):
		self.clear_widgets()
		self.DataImageSource = self.DataList[self.NowImage]
		self.ShowImage()
		self.ShowButtons()
		self.ShowCheckBoxes()
		self.ClearSelection()
		self.SetAnnotText()

	def ShowImage(self):
		if not(exists(self.DataImageSource[:-3] + "json")):
			# Creates temporary json file so if application get crashed in middle of annotation, you can resume it
			self.LightClasses = {"class":self.DefaulDict,"status":0}
			self.write_json(self.LightClasses,self.DataImageSource[:-3] + "json")
		else:
			self.LightClasses = self.read_json(self.DataImageSource[:-3] + "json")
			if(self.LightClasses["status"]==1):
				self.OpenNextImage()
				return
		# making grid and inserting image.     Easy for positioning of Image
		self.ImageGrid = GridLayout(cols=1,size_hint=(self.DataW,self.DataH),pos_hint={"center_x":self.DataX,"center_y":self.DataY})
		source = self.DataImageSource
		print(source)
		self.DataImage = ImageButton(source=source,keep_ratio=True,allow_stretch=True)
		self.ImageGrid.add_widget(self.DataImage)
		self.add_widget(self.ImageGrid)

	def ShowButtons(self):
		# making save, delete and clear selection buttons
		CorrectBtn = Button(text="CORRECT",font_size=25,size_hint=(self.CorrectW,self.CorrectH),pos_hint={"center_x":self.CorrectX,"center_y":self.CorrectY},valign="center",halign="center",on_press=partial(self.SaveImage,True))
		self.add_widget(CorrectBtn)
		WrongBtn = Button(text="WRONG",font_size=25,size_hint=(self.WrongW,self.WrongH),pos_hint={"center_x":self.WrongX,"center_y":self.WrongY},valign="center",halign="center",on_press=partial(self.SaveImage,False))
		self.add_widget(WrongBtn)

		ClearBtn = Button(text="CLEAR",font_size=25,size_hint=(self.ClearW,self.ClearH),pos_hint={"center_x":self.ClearX,"center_y":self.ClearY},valign="center",halign="center",on_press=partial(self.ClearSelection))
		self.add_widget(ClearBtn)

	def ShowCheckBoxes(self):
		# annotation text and annotation list
		self.AnnotBtn = Button(text="CORRECT",font_size=25,size_hint=(self.AnnotW,self.AnnotH),pos_hint={"center_x":self.AnnotX,"center_y":self.AnnotY},valign="center",halign="center",background_color=(0,0,0,1))
		self.SetAnnotText()
		self.add_widget(self.AnnotBtn)

		self.play = ScrollView(size_hint=(self.ListW, self.ListH),pos_hint={"center_x":self.ListX,"center_y":self.ListY}, size=(Window.width, Window.height))
		self.roll = GridLayout(cols=3, spacing=20, size_hint_y=None,padding=20)
		self.roll.bind(minimum_height=self.roll.setter('height'))

		self.play.add_widget(self.roll)
		self.add_widget(self.play)

		self.CheckBoxes = {}

		for i in range(len(self.Lights)):
			num_label = Button(text=str(i+1),font_size=20,size_hint=(0.1,None),background_color=(0,0,0,1))
			num_label.bind(width=lambda s,w: s.setter("text_size")(s,(w,None)))
			num_label.bind(texture_size=num_label.setter("size"))
			self.roll.add_widget(num_label)

			LightCheckBox = CheckBox(size_hint_x=0.3)
			self.CheckBoxes[i] = LightCheckBox
			self.roll.add_widget(self.CheckBoxes[i])

			self.CheckBoxes[i].active = bool(self.LightClasses["class"][i])

			name_label = Button(text=str(self.Lights[i]),font_size=20,size_hint=(0.6,None),background_color=(0,0,0,1),on_press=partial(self.ToggleCheckBox,i))
			name_label.bind(width=lambda s,w: s.setter("text_size")(s,(w,None)))
			name_label.bind(texture_size=name_label.setter("size"))			
			self.roll.add_widget(name_label)

	def SaveImage(self,Val,_="_"):
		# saving or deleting image depending upon Val
		if(Val):
			SaveAt = self.SaveDataDir + self.DataImageSource[len(self.LoadDataDir):]
			self.ensure_dir(SaveAt)
			move(self.DataImageSource, SaveAt)
			print(self.DataImageSource[:-3]+"json")
			remove(self.DataImageSource[:-3]+"json")
			self.LightClasses["status"] = 1
			for i in range(len(self.CheckBoxes)):
				 self.LightClasses["class"][i] = int(self.CheckBoxes[i].active)
			self.write_json(self.LightClasses, self.SaveDataDir + self.DataImageSource[len(self.LoadDataDir):-3] + "json")
		else:
			SaveAt = self.SaveDataDir + self.DataImageSource[len(self.LoadDataDir):]
			self.ensure_dir(SaveAt)
			move(self.DataImageSource, SaveAt)
			print(self.DataImageSource[:-3]+"json")
			remove(self.DataImageSource[:-3]+"json")
			self.LightClasses["status"] = 2
			for i in range(len(self.CheckBoxes)):
				 self.LightClasses["class"][i] = int(self.CheckBoxes[i].active)
			self.write_json(self.LightClasses, self.SaveDataDir + self.DataImageSource[len(self.LoadDataDir):-3] + "json")
		self.OpenNextImage()

	def OpenNextImage(self):
		if(self.NowImage<len(self.DataList)-1):
			self.NowImage += 1
			self.cust_pre_enter()
		else:
			self.NowImage += 1
			self.clear_widgets()
			self.add_widget(Label(text="Thank You",font_size=40))

	def ToggleCheckBox(self,num,_="_"):
		# changing annoatation of particular class
		self.CheckBoxes[num].active = not(self.CheckBoxes[num].active)
		self.LightClasses["class"][num] = int(self.CheckBoxes[num].active)
		self.write_json(self.LightClasses, self.DataImageSource[:-3] + "json")
		self.SetAnnotText()

	def ClearSelection(self,_="_"):
		for i in range(len(self.CheckBoxes)):
			self.CheckBoxes[i].active = False
			self.LightClasses["class"][i] = 0
		self.write_json(self.LightClasses, self.DataImageSource[:-3] + "json")
		self.SetAnnotText()

	def SetAnnotText(self):
		# changing annotation text 
		text = ""
		for i in range(len(self.LightClasses["class"])):
			text += str(self.LightClasses["class"][i])
		self.AnnotBtn.text = text

	def ensure_dir(self,file_path):
		if '/' in file_path:
			directory = dirname(file_path)
			if not exists(directory):
				makedirs(directory)

	def read_json(self,filename):
		input_file = open(filename)
		json_array = j_load(input_file)
		return json_array

	def write_json(self,dict_,file_path):
		print(file_path)
		self.ensure_dir(file_path)
		j_dump(dict_, co_open(file_path, 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True, indent=4)

	def get_folders(self,root_folder):
		folders = []
		folders.append(root_folder)
		for (dirpath, dirnames, filenames) in walk(root_folder):
			for fold in dirnames:
				folders.append(dirpath + fold + '/')
		return(folders)

	def get_files(self,folders,ext):
		files = []
		for folder in folders:
			files_fold = ([(folder+i) for i in listdir(folder) if i.endswith(ext)])
			files_fold.sort()
			for filename in files_fold:
				files.append(filename)
		return(files)

class MainClass(App):
	def build(self):
		ScreenMan = ScreenManagerbuild()

		ScreenMan.add_widget(HomeScreen(name='home_window'))

		return ScreenMan

class ScreenManagerbuild(ScreenManager):
	pass

if __name__ == '__main__':
	MainClass().run()
