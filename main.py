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
import logging
import asyncio

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.properties import DictProperty
from kivy.properties import StringProperty
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.base import runTouchApp
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooser
from kivy.logger import Logger
from kivy.clock import Clock


from pynput.keyboard import Listener as Key_listener
from pynput.mouse import Listener as Mouse_listener
from PIL import ImageGrab
import numpy as np
import plyer

import pixelAct 
import inputAct 

TITLE = 'JARVIS_UI'
WINDOW = None
DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CONFIG_PATH = f'{DIR}\conf'
INI_FILE = f'{DIR}\init.yaml'

GENERIC_ELEMENT_FIELDS = {
    'enabled': True
}

TYPE_TO_GET_FUNCTION = None
TYPE_TO_CONF_KEY = {
    'pixel_act': 'pixelAct',
    'stop_pixel': 'stop_pixels',
    'run_pixel': 'run_pixels',
    'input_act': 'inputAct',
}        
BUTTON_TEXT_TO_TYPE = {
    "PixelAct": 'pixel_act',
    "RunPixels": 'run_pixel',
    "StopPixels": 'stop_pixel',
    "InputAct": 'input_act',
} 

CHAR_TO_PROTECT = {
    '"': '\x22',
    "'": '\x27',
}

def protect_text_input(_str):
    global CHAR_TO_PROTECT
    result = _str
    for char, sub in CHAR_TO_PROTECT.items():
        result = result.replace(char, sub)
    return result

FIELDS = {
    'name': {
        'func': protect_text_input,
        'default_value': '',
    },
    'enabled': {
        'func': eval,
        'default_value': True,
    },
    'on_change': {
        'func': eval,
        'default_value': True,
    },
    'x': {
        'func': int,
        'default_value': 0,
    },
    'y': {
        'func': int,
        'default_value': 0,
    },
    'color': {
        'func': eval,
        'default_value': [0, 0, 0],
    },
    'actions': {
        'func': protect_text_input,
        'default_value': '',
    },
    'action_mode': {
        'func': protect_text_input,
        'default_value': 'all',
    },
    'cool_down': {
        'func': float,
        'default_value': 10.0,
    },
    'group_id': {
        'func': protect_text_input,
        'default_value': 'default',
    },
    'time_pressed': {
        'func': float,
        'default_value': 1.0,
    },
    'input': {
        'func': protect_text_input,
        'default_value': 'Button.left',
    },
    'color_margin': {
        'func': int,
        'default_value': 20,
    },
}

TYPE_TO_FIELDS = {
    'pixel_act': {
        'name': FIELDS['name'],
        'enabled': FIELDS['enabled'],
        'on_change': FIELDS['on_change'],
        'x': FIELDS['x'],
        'y': FIELDS['y'],
        'color': FIELDS['color'],
        'actions': FIELDS['actions'],
        'action_mode': FIELDS['action_mode'],
        'cool_down': FIELDS['cool_down'],
        'color_margin': FIELDS['color_margin'],
    },
    'stop_pixel': {
        'name': FIELDS['name'],
        'enabled': FIELDS['enabled'],
        'x': FIELDS['x'],
        'y': FIELDS['y'],
        'color': FIELDS['color'],
        'group_id': FIELDS['group_id'],
        'color_margin': FIELDS['color_margin'],
    },
    'run_pixel': {
        'name': FIELDS['name'],
        'enabled': FIELDS['enabled'],
        'x': FIELDS['x'],
        'y': FIELDS['y'],
        'color': FIELDS['color'],
        'color_margin': FIELDS['color_margin'],
    },
    'input_act': {
        'name': FIELDS['name'],
        'enabled': FIELDS['enabled'],
        'time_pressed': FIELDS['time_pressed'],
        'input': FIELDS['input'],
        'actions': FIELDS['actions'],
        'action_mode': FIELDS['action_mode'],
        'cool_down': FIELDS['cool_down'],
    },
}

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
        
class Popup_content(AnchorLayout):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        size=(300, 300)
        self.add_widget(
            TextInput(
                text = msg,
                halign = "center",               
            )
        )
   
class MainWidget(BoxLayout):  
    
    curr_object = DictProperty(rebind=True)
    logs = StringProperty('')
    selected_file = StringProperty('')
    
    def __init__(self, *args, **kwargs):
        global TYPE_TO_GET_FUNCTION
        super().__init__(*args, **kwargs)
        self.config = {}
        self.key_listener = Key_listener(on_press=self.on_press)
        self.mouse_listener = Mouse_listener(on_click=self.on_click)
        
        self.validate_pixel_creation = False
        self.request_validate = False
        
        self.last_clicked_pixel = {}
        self.new_input = {}
      
        self.pixel_act = None
        self.inupt_act = None

        self.pixel_creation_popup = None

        Logger.level = logging.INFO
        custom_handler = MyHandler(self.upadte_logs, logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        custom_handler.setFormatter(formatter)
        Logger.addHandler(custom_handler)        
        self.logger = Logger 
        self.config_path = ''
        self.laod_vars_from_init()
        self.selected_file = self.config_path
        
        
        TYPE_TO_GET_FUNCTION = {
            'pixel_act': self.request_pixel_at_click,
            'stop_pixel': self.request_pixel_at_click,
            'run_pixel': self.request_pixel_at_click,
            'input_act': self.request_input_act,
        }
 
    def laod_vars_from_init(self):
        global INI_FILE
        try:
            with open(INI_FILE, encoding='utf8') as file:
                ini_conf = yaml.safe_load(file.read())
            self.config_path = ini_conf.get('last_selected_conf_file')
        except: pass

    def save_vars_to_init(self):
        ini_conf = {}
        ini_conf['last_selected_conf_file'] = self.config_path
        with open(INI_FILE, 'w') as outfile:
            yaml.dump(ini_conf, outfile, default_flow_style=False)

    def upadte_logs(self, msg, _):
        self.logs = f'{self.logs}\n{msg}'
    
    def get_config(self, force=False):
        if not self.config_path: return {}
        if not self.config or force: 
            try:
                with open(self.config_path, encoding='utf8') as file:
                    self.config = yaml.safe_load(file.read()) or {}
                    self.logger.info(f'sucessfully loaded config file {self.config_path}')
            except Exception as e: 
                self.logger.info(f'Failed to load config file {self.config_path}: {e}')
                self.config = {} 
        return self.config 

    def save_config(self):
        global CONFIG
        if self.config_path:
            with open(self.config_path, 'w') as outfile:
                yaml.dump(self.get_config(), outfile, default_flow_style=False)
                self.logger.info(f'sucessfully saved config file')

    def show_popup(self, err_msg, title = "Error", auto_dismiss = True):
        popupWindow = Popup(
            title=title, 
            content=Popup_content(err_msg), 
            auto_dismiss=auto_dismiss, 
            size_hint=(None,None),
            size=(400,400)
        ) 
        popupWindow.open()
        return popupWindow
    
    def display_page(self, button, pages_layout, page):
        pages_layout.remove_widget(page)
        pages_layout.add_widget(page, 0)
        self.update_curr_object({}, None)
        self.update_page(button) 
 
    def update_page(self, button):
        global BUTTON_TEXT_TO_TYPE
        type = BUTTON_TEXT_TO_TYPE.get(button.text)
        if type:
            self.update_elements_page(type)
            return 
        if button.text == "Load":
            self.update_config_choice_page()

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

            self.last_clicked_pixel['x'] = x
            self.last_clicked_pixel['y'] = y
            self.last_clicked_pixel['name'] = f'{x}_{y}_{color_val}'
            self.last_clicked_pixel['color'] = color_val

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

    def is_name_taken(self, name):
        for section, elements in self.get_config().items():
            for element in elements:
                if element.get('name', '') == name:
                    return True
        return False

    def start_mouse_listener(self):
        self.mouse_listener.start()

    def stop_mouse_listener(self):
        self.mouse_listener.stop()
        del self.mouse_listener
        self.mouse_listener = Mouse_listener(on_click=self.on_click)
            
    def request_input_act(self):
        return {
            'name': ''
        }
    
    def request_pixel_at_click(self):
        if not self.pixel_creation_popup:
            self.pixel_creation_popup = self.show_popup(
                "Please click to create a pixel", 
                title="Pixel creation",
                auto_dismiss=False
            )
        return self.last_clicked_pixel.copy()

    def abord_error(self, msg):
        self.show_popup(msg)
        self.logger.error(msg)
        return False

    def update_elements_page(self, type):
        global TYPE_TO_CONF_KEY
        list_widget = getattr(self.ids, f'{type}_list')
        list_widget.clear_widgets()
        for element in self.get_config().get(TYPE_TO_CONF_KEY[type], []):
            button = ToggleButton(
                text=element['name'],
                size_hint=(None, None),
                size=('160dp', '35dp'), 
                pos_hint ={'center_x':0.5},
                group='all_list',
            )
            func = partial(self.update_curr_object, element)
            button.bind(on_press=func)
            anchor = AnchorLayout(
                size_hint=(1, None),
                height='40dp',
            )
            anchor.add_widget(button)
            list_widget.add_widget(anchor)   
        self.click_on_last_element_button(type)
        
    def create_element(self, type, _):
        global GENERIC_ELEMENT_FIELDS
        global TYPE_TO_FIELDS
        global TYPE_TO_GET_FUNCTION
        global TYPE_TO_CONF_KEY
        
  
        element = TYPE_TO_GET_FUNCTION[type]()
        
        if not element: return True
        self.last_clicked_pixel = {}
        self.stop_mouse_listener()
        if self.pixel_creation_popup: self.pixel_creation_popup.dismiss()
        self.pixel_creation_popup = None
        
        if self.is_name_taken(element['name']):
            self.abord_error(
                f'Name: {element["name"]} already taken in conf, names must be unique'
            )
            return False
        element.update(GENERIC_ELEMENT_FIELDS)
        
        update_dict = {}
        for field, field_info in TYPE_TO_FIELDS[type].items():
            if field not in element:
                update_dict[field] = field_info['default_value']
                
        element.update(update_dict)
        
        self.get_config().setdefault(TYPE_TO_CONF_KEY[type], []).append(element)
        self.update_curr_object(element, None)
        
        self.update_elements_page(type)
        return False
            
    def request_element_creation(self, type):
        self.last_clicked_pixel = {}
        self.start_mouse_listener()
        Clock.schedule_interval(partial(self.create_element, type), 0.3)
        
    def delete_curr_element(self, type):
        global TYPE_TO_CONF_KEY
        del_i = self.find_index_by_name(
            self.get_config().get(TYPE_TO_CONF_KEY[type], []),
            self.curr_object.get('name', '')
        )
        if del_i is not None:
            del self.get_config()[TYPE_TO_CONF_KEY[type]][del_i]
            pops = list(self.curr_object.keys())
            for ele in pops:
                del self.curr_object[ele]
            self.update_elements_page(type)
            self.click_on_last_element_button(type)
               
    def upadte_element_config(self, type):
        global TYPE_TO_FIELDS
        global TYPE_TO_CONF_KEY
        element = {}
        
        try:
            name = getattr(self.ids, f'{type}_name').text
            if name:
                for field, filed_info in TYPE_TO_FIELDS[type].items():
                    func = filed_info['func']
                    if func is None:
                        element[field] = getattr(self.ids, f'{type}_{field}').text
                    else:
                        element[field] = func(getattr(self.ids, f'{type}_{field}').text)              
        except:
            self.abord_error(
                f'Error while saving {type} {element}'
                f'make sure that number fields conatin numbers'
                f'and other fields contain words'
            )
        if element: 
            self.delete_curr_element(type)
            self.get_config().setdefault(TYPE_TO_CONF_KEY[type], []).append(element)
        self.update_elements_page(type)
        self.save_config()         

    def click_on_last_element_button(self, type):
        list_widget = getattr(self.ids, f'{type}_list')
        if list_widget.children:
            last_anchor = list_widget.children[0]
            last_button = last_anchor.children[0]
            last_button.trigger_action()
            last_button.state = 'down'

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
    
    def update_config_choice_page(self):
        pass

    def get_config_path(self):
        global DIR
        return self.config_path or f'{DIR}\conf'
    
    def load_config(self):
        global DEFAULT_CONFIG_PATH
        
        if self.config_path:
            config_directory = os.path.dirname(self.config_path)
        else:
            config_directory = DEFAULT_CONFIG_PATH
            
        selected_files = plyer.filechooser.open_file(path=config_directory)
        
        if not selected_files:  
            return 
            
        selected_file = selected_files[0]
        allowed_extentions = [
            'yaml',
            'yml'
        ]
        
        for enxtention in allowed_extentions:
            if selected_file.endswith(enxtention): break 
        else:
            msg =   f'{selected_file} -> bad file format\nPlease select a yaml file'
            return self.abord_error(msg)
        
        self.config_path = selected_file
        self.selected_file = selected_file
        self.save_vars_to_init()

class MainApp(App):
        
    def on_start(self, *args):
        global TITLE, WINDOW
        Window.set_title(TITLE)
        WINDOW = win32gui.FindWindow(None, TITLE)

if __name__ == "__main__":

    MainApp().run()
    
    # mw = MainWidget()
    # mw.run()