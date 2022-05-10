# -*- coding: utf-8 -*-

import os
# os.environ["KIVY_NO_CONSOLELOG"] = "1"


import yaml
import json
import time 
from pathlib import Path
from functools import partial
import win32gui
import win32con

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.properties import DictProperty
from kivy.properties import StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.base import runTouchApp
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.clock import Clock
import logging


from pynput.keyboard import Listener as Key_listener
TITLE = 'JARVIS_UI'
WINDOW = None
from pynput.mouse import Listener as Mouse_listener
from PIL import ImageGrab
import numpy as np

import pixelAct 
import inputAct 


CONFIG_PATH = f'{os.path.dirname(os.path.realpath(__file__))}/config.yaml'


def pprint(s):
    print(
        json.dumps(
            s,
            indent=2
        )
    )

class MyHandler(logging.Handler):
    def __init__(self, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func
        
    def emit(self, record):
        try:
            msg = self.format(record)

            Clock.schedule_once(partial(self.func, msg))
        except Exception as e : print('--**-- ERROR', e)
        
class Error_popup_content(AnchorLayout):
    def __init__(self, err_msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        size=(300, 300)
        self.add_widget(
            TextInput(
                text = err_msg,
                halign = "center",               
            )
        )
   
class MainWidget(BoxLayout):  
    
    curr_object = DictProperty(rebind=True)
    logs = StringProperty()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None
        self.key_listener = Key_listener(on_press=self.on_press)
        self.mouse_listener = Mouse_listener(on_click=self.on_click)
        
        self.validate_pixel_creation = False
        self.request_validate = False
        
        self.new_pixel = {}
        self.new_input = {}
      
        self.pixel_act = None
        self.inupt_act = None

        Logger.level = logging.INFO
        custom_handler = MyHandler(self.upadte_logs, logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        custom_handler.setFormatter(formatter)
        Logger.addHandler(custom_handler)        
        self.logger = Logger 

                
        
    def upadte_logs(self, msg, _):
        self.logs = f'{self.logs}\n{msg}'
    
    def get_config(self):
        global CONFIG_PATH, CONFIG
        if self.config is None: 
            # self.config = yaml.safe_load(CONFIG)
            with open(CONFIG_PATH, encoding='utf8') as file:
                self.config = yaml.safe_load(file.read())
        return self.config

    def save_config(self):
        global CONFIG
        with open(CONFIG_PATH, 'w') as outfile:
            yaml.dump(self.get_config(), outfile, default_flow_style=False)

    def show_popup(self, err_msg):
        popupWindow = Popup(
            title="Error", 
            content=Error_popup_content(err_msg), 
            size_hint=(None,None),
            size=(400,400)
        ) 
        popupWindow.open()
    
    def display_page(self, button, pages_layout, page):
        pages_layout.remove_widget(page)
        pages_layout.add_widget(page, 0)
        self.update_curr_object({}, None)
        self.update_page(button) 
 
    def update_page(self, button):
        if button.text == "PixelAct":
            self.update_pixel_act_page()
        if button.text == "RunPixels":
            self.update_run_pixel_page()
        if button.text == "StopPixels":
            self.update_stop_pixel_page()
        if button.text == "InputAct":
            self.update_input_act_page()

    def on_click(self, x, y, button, pressed):
        if pressed:
            image = ImageGrab.grab(None)
            image = np.array(image)
            color = image[y, x].tolist()
            color_val = [
                color[0],
                color[1],
                color[2],
            ]

            self.new_pixel['x'] = x
            self.new_pixel['y'] = y
            self.new_pixel['name'] = f'{x}_{y}_{color_val}'
            self.new_pixel['enabled'] = False
            self.new_pixel['color'] = color_val

    def on_press(self, button):
        pass

    def find_index_by_name(self, a_list_of_dict, name):
        for i, elem in enumerate(a_list_of_dict):
            if elem.get('name', '') == name:
                return i

    def update_curr_object(self, infos, _):
        self.curr_object.clear()
        for k, v in infos.items():
            self.curr_object[k] = str(v)

    ### pixel_act
    def create_pixel_act(self):
        self.mouse_listener.start()
        while not self.new_pixel:
            self.logger.info('click to create a pixel act')
            time.sleep(0.3)
        self.mouse_listener.stop()
        del self.mouse_listener
        self.mouse_listener = Mouse_listener(on_click=self.on_click)
        
        
        exist_i = self.find_index_by_name(
            self.get_config().get('pixelAct', []),
            self.new_pixel.get('name', '')
        )
        
        if exist_i is None:
            self.new_pixel.update(
                {
                    'actions': '',
                    'action_mode': 'all',
                    'cool_down': 10,
                }
            )
            self.get_config().setdefault('pixelAct', []).append(self.new_pixel)
            self.update_curr_object(self.new_pixel, None)
        else:
            self.show_popup(
                f'Name {self.new_pixel["name"]} '
                f'already taken !'
            )
        self.new_pixel = {}
        self.update_pixel_act_page()

    def update_pixel_act_config(self):
        pixel = {}
        try:
            if self.ids.pixel_act_name.text: 
                pixel['name'] = self.ids.pixel_act_name.text
                pixel['x'] = int(self.ids.pixel_act_x.text)
                pixel['y'] = int(self.ids.pixel_act_y.text)
                pixel['actions'] = self.ids.pixel_act_actions.text
                pixel['action_mode'] = self.ids.pixel_act_action_mode.text
                pixel['cool_down'] = float(self.ids.pixel_act_cool_down.text)
                pixel['on_change'] = eval(self.ids.pixel_act_on_change.text)
                pixel['enabled'] = eval(self.ids.pixel_act_enabled.text)
                pixel['color'] = eval(self.ids.pixel_act_color.text)
        except:
            self.show_popup(
                f'Error while saving the pixel {pixel["name"]} '
                f'make sure that number fields conatin numbers'
                f'and other fields contain words'
            )
            return 
        if pixel: 
            self.delete_curr_pixel_act()
            self.get_config()['pixelAct'].append(pixel)
        self.update_pixel_act_page()
        self.save_config()

    def delete_curr_pixel_act(self):
        pixel_to_del_i = self.find_index_by_name(
            self.get_config().get('pixelAct', []),
            self.curr_object.get('name', '')
        )
        if pixel_to_del_i is not None:
            del self.get_config()['pixelAct'][pixel_to_del_i]
            pops = list(self.curr_object.keys())
            for ele in pops:
                del self.curr_object[ele]
            self.update_pixel_act_page()
        
    def update_pixel_act_page(self):
        list_widget = self.ids.pixel_act_list
        list_widget.clear_widgets()
        for pixel in self.get_config().get('pixelAct', []):
            button = Button(
                text=pixel['name'],
                size_hint=(None, None),
                size=('160dp', '35dp'),
                pos_hint ={'center_x':0.5}
            )
            func = partial(self.update_curr_object, pixel)
            button.bind(on_press=func)
            anchor = AnchorLayout(
                size_hint=(1, None),
                height='40dp',
            )
            anchor.add_widget(button)
            list_widget.add_widget(anchor)

    ### run_pixel
    def create_run_pixel(self):
        self.mouse_listener.start()
        while not self.new_pixel:
            print('click to create a run pixel')
            time.sleep(0.3)
        self.mouse_listener.stop()
        del self.mouse_listener
        self.mouse_listener = Mouse_listener(on_click=self.on_click)
        
        
        exist_i = self.find_index_by_name(
            self.get_config().get('run_pixels', []),
            self.new_pixel.get('name', '')
        )
        
        if exist_i is None:
            self.get_config().setdefault('run_pixels', []).append(self.new_pixel)
            self.update_curr_object(self.new_pixel, None)
        else:
            self.show_popup(
                f'Name {self.new_pixel["name"]} '
                f'already taken !'
            )
        self.new_pixel = {}
        self.update_run_pixel_page()

    def update_run_pixel_config(self):
        pixel = {}
        try:
            if self.ids.run_pixel_name.text: 
                pixel['name'] = self.ids.run_pixel_name.text
                pixel['x'] = int(self.ids.run_pixel_x.text)
                pixel['y'] = int(self.ids.run_pixel_y.text)
                pixel['enabled'] = eval(self.ids.run_pixel_enabled.text)
                pixel['color'] = eval(self.ids.run_pixel_color.text)
        except:
            self.show_popup(
                f'Error while saving the pixel {pixel["name"]} '
                f'make sure that number fields conatin numbers'
                f'and other fields contain words'
            )
            return 
        if pixel: 
            self.delete_curr_run_pixel()
            self.get_config()['run_pixels'].append(pixel)
        self.update_run_pixel_page()
        self.save_config()

    def delete_curr_run_pixel(self):
        pixel_to_del_i = self.find_index_by_name(
            self.get_config().get('run_pixels', []),
            self.curr_object.get('name', '')
        )
        if pixel_to_del_i is not None:
            del self.get_config()['run_pixels'][pixel_to_del_i]
            pops = list(self.curr_object.keys())
            for ele in pops:
                del self.curr_object[ele]
            self.update_run_pixel_page()
        
    def update_run_pixel_page(self):
        list_widget = self.ids.run_pixel_list
        list_widget.clear_widgets()
        for pixel in self.get_config().get('run_pixels', []):
            button = Button(
                text=pixel['name'],
                size_hint=(None, None),
                size=('160dp', '35dp'),
                pos_hint ={'center_x':0.5}
            )
            func = partial(self.update_curr_object, pixel)
            button.bind(on_press=func)
            anchor = AnchorLayout(
                size_hint=(1, None),
                height='40dp',
            )
            anchor.add_widget(button)
            list_widget.add_widget(anchor)

    ### stop_pixel
    def create_stop_pixel(self):
        self.mouse_listener.start()
        while not self.new_pixel:
            print('click to create a stop pixel')
            time.sleep(0.3)
        self.mouse_listener.stop()
        del self.mouse_listener
        self.mouse_listener = Mouse_listener(on_click=self.on_click)
        
        
        exist_i = self.find_index_by_name(
            self.get_config().get('stop_pixels', []),
            self.new_pixel.get('name', '')
        )
        
        if exist_i is None:
            self.new_pixel.update(
                {
                    'group_id': 'default',
                }
            )
            self.get_config().setdefault('stop_pixels', []).append(self.new_pixel)
            self.update_curr_object(self.new_pixel, None)
        else:
            self.show_popup(
                f'Name {self.new_pixel["name"]} '
                f'already taken !'
            )
        self.new_pixel = {}
        self.update_stop_pixel_page()

    def update_stop_pixel_config(self):
        pixel = {}
        try:
            if self.ids.stop_pixel_name.text: 
                pixel['name'] = self.ids.stop_pixel_name.text
                pixel['x'] = int(self.ids.stop_pixel_x.text)
                pixel['y'] = int(self.ids.stop_pixel_y.text)
                pixel['enabled'] = eval(self.ids.stop_pixel_enabled.text)
                pixel['color'] = eval(self.ids.stop_pixel_color.text)
                pixel['group_id'] = self.ids.stop_pixel_group_id.text
        except:
            self.show_popup(
                f'Error while saving the pixel {pixel["name"]} '
                f'make sure that number fields conatin numbers'
                f'and other fields contain words'
            )
            return 
        if pixel: 
            self.delete_curr_stop_pixel()
            self.get_config()['stop_pixels'].append(pixel)
        self.update_stop_pixel_page()
        self.save_config()

    def delete_curr_stop_pixel(self):
        pixel_to_del_i = self.find_index_by_name(
            self.get_config().get('stop_pixels', []),
            self.curr_object.get('name', '')
        )
        if pixel_to_del_i is not None:
            del self.get_config()['stop_pixels'][pixel_to_del_i]
            pops = list(self.curr_object.keys())
            for ele in pops:
                del self.curr_object[ele]
            self.update_stop_pixel_page()
        
    def update_stop_pixel_page(self):
        list_widget = self.ids.stop_pixel_list
        list_widget.clear_widgets()
        for pixel in self.get_config().get('stop_pixels', []):
            button = Button(
                text=pixel['name'],
                size_hint=(None, None),
                size=('160dp', '35dp'),
                pos_hint ={'center_x':0.5}
            )
            func = partial(self.update_curr_object, pixel)
            button.bind(on_press=func)
            anchor = AnchorLayout(
                size_hint=(1, None),
                height='40dp',
            )
            anchor.add_widget(button)
            list_widget.add_widget(anchor)

    ### input act
    def create_input_act(self):
        
        try:
            if self.ids.input_act_name.text: 
                self.new_input['name'] = self.ids.input_act_name.text
                self.new_input['actions'] = self.ids.input_act_actions.text
                self.new_input['action_mode'] = self.ids.input_act_action_mode.text
                self.new_input['cool_down'] = float(self.ids.input_act_cool_down.text)
                self.new_input['time_pressed'] = float(self.ids.input_act_time_pressed.text)
                self.new_input['input'] = self.ids.input_act_input.text
                self.new_input['enabled'] = eval(self.ids.input_act_enabled.text)
        except:
            msg =   f'Error while saving input act {self.new_input["name"]} '+\
                    f'make sure that number fields conatin numbers '+\
                    f'and other fields contain words'
            self.show_popup(msg)
            self.logger.error(msg)
            self.new_input = {}
            return 
        
        if not self.new_input.get('name'):
            msg =   f'Error while saving inpu, name cannot be empty'
            self.show_popup(msg)
            self.logger.error(msg)
            return 
            
        exist_i = self.find_index_by_name(
            self.get_config().get('inputAct', []),
            self.new_input.get('name', '')
        )
        
        if exist_i is None:
            self.get_config().setdefault('inputAct', []).append(self.new_input)
            self.update_curr_object(self.new_input, None)
        else:
            self.show_popup(
                f'Name {self.new_input["name"]} '
                f'already taken !'
            )
        self.new_input = {}
        self.update_input_act_page()

    def update_input_act_config(self):
        input_act = {}
        try:
            if self.ids.input_act_name.text: 
                input_act['name'] = self.ids.input_act_name.text
                input_act['actions'] = self.ids.input_act_actions.text
                input_act['action_mode'] = self.ids.input_act_action_mode.text
                input_act['cool_down'] = float(self.ids.input_act_cool_down.text)
                input_act['time_pressed'] = float(self.ids.input_act_time_pressed.text)
                input_act['input'] = self.ids.input_act_input.text
                input_act['enabled'] = eval(self.ids.input_act_enabled.text)
        except:
            msg =   f'Error while saving input act {input_act["name"]} '+\
                    f'make sure that number fields conatin numbers '+\
                    f'and other fields contain words'
            self.show_popup(msg)
            self.logger.error(msg)
            return 
        if input_act: 
            self.delete_curr_input_act()
            self.get_config()['inputAct'].append(input_act)
        self.update_input_act_page()
        self.save_config()

    def delete_curr_input_act(self):
        pixel_to_del_i = self.find_index_by_name(
            self.get_config().get('inputAct', []),
            self.curr_object.get('name', '')
        )
        if pixel_to_del_i is not None:
            del self.get_config()['inputAct'][pixel_to_del_i]
            pops = list(self.curr_object.keys())
            for ele in pops:
                del self.curr_object[ele]
            self.update_input_act_page()
        
    def update_input_act_page(self):
        list_widget = self.ids.input_act_list
        list_widget.clear_widgets()
        for input_act in self.get_config().get('inputAct', []):
            button = Button(
                text=input_act['name'],
                size_hint=(None, None),
                size=('160dp', '35dp'),
                pos_hint ={'center_x':0.5}
            )
            func = partial(self.update_curr_object, input_act)
            button.bind(on_press=func)
            anchor = AnchorLayout(
                size_hint=(1, None),
                height='40dp',
            )
            anchor.add_widget(button)
            list_widget.add_widget(anchor)

    ### Engine
    def run(self):
        self.pixel_act = pixelAct.PixelAct(self.get_config()) 
        self.inupt_act = inputAct.InputAct(self.get_config())
        
        permission_function = self.pixel_act.get_permission
        
        self.pixel_act.request_permission = permission_function
        self.inupt_act.request_permission = permission_function
        
        self.pixel_act.start()
        self.inupt_act.start()
        self.logger.info('Started')
    
    def stop(self):
        self.pixel_act.stop()
        del self.pixel_act
        self.pixel_act = None
        
        self.inupt_act.stop()
        del self.inupt_act
        self.inupt_act = None       
        
        self.logger.info('Stopped')

    ### misc
    def always_on_top(self):
        global TITLE, WINDOW
        
        rect = win32gui.GetWindowRect(WINDOW)
        
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y

        win32gui.SetWindowPos(WINDOW, win32con.HWND_TOPMOST, x, y, w, h, 0)
        
    def not_always_on_top(self):
        global TITLE, WINDOW
        
        rect = win32gui.GetWindowRect(WINDOW)
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y

        win32gui.SetWindowPos(WINDOW, win32con.HWND_NOTOPMOST, x, y, w, h, 0)

class MainApp(App):
        
    def on_start(self, *args):
        global TITLE, WINDOW
        Window.set_title(TITLE)
        WINDOW = win32gui.FindWindow(None, TITLE)

if __name__ == "__main__":

    MainApp().run()
    
    # mw = MainWidget()
    # mw.run()