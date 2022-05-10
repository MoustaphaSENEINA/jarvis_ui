# -*- coding: utf-8 -*-

import time
from pynput.keyboard import Listener as Key_listener
from pynput.mouse import Listener as Mouse_listener
from pynput.mouse import Button as MButton
from pynput.mouse import Controller as MController
from threading import Thread
import json
import act


class InputAct(act.Act):

    def __init__(self, config):
    
        super().__init__()
        
        self.kl = Key_listener(on_press=self.on_press)
        self.ml = Mouse_listener(on_click=self.on_click)
        self.key_orders = self.get_key_orders_from_list(
            config.get("inputAct", [])
        )      
        self.history = {}
        self.call_stop_functions = []
        self.seekAndClick_orders = config.get("seekAndClick", {})
        self.loop_frequency = 0.05
        self.retry_frequency = 1
        self.mouse = MController()
        self.left_clicks_history = []
        self.reset_left_clicks_history()

    def get_key_orders_from_list(self, conf):
        key_orders = {}
        for order in conf:
            key = order.get('input')
            key_orders.setdefault(key, []).append(order)
        return key_orders
    
    
    def reset_left_clicks_history(self):
        self.left_clicks_history = [
            0,
            0,
            0,
            0,
            0,
            0,
        ]      

    def on_click(self, x, y, button, pressed):
        
        if not self.request_permission(): 
            self.history = {}
            return
            
        button_str = str(button)
        now = time.time()
        if pressed:
            self.history[button_str] = now
        else:

            if button_str == 'Button.left':
                self.left_clicks_history.append(now)
                del self.left_clicks_history[0]
                
            try: del self.history[button_str]
            except: pass

    def on_press(self, button):
        
        button = str(button)[1:-1]
        self.history[button] = time.time()

        if str(button) in self.seekAndClick_orders:
            y, x = self.request_color_position(
                self.seekAndClick_orders[button].get('color', [0, 0, 0])
            )
            
            if x:   
                self.log('seekAndClick_orders -> work in progress')
                # mx, my = win32api.GetCursorPos()
                # print ('---', x, y, '""', mx, my)

                # x = x - mx 
                # y = y - my 
                # print ('--- ==== ', x, y)
                # ctypes.windll.user32.mouse_event(0x8001, x*2, y*2, 0, 0)

                # self.mouse.press(MButton.left)
                # time.sleep(0.1)
                # self.mouse.release(MButton.left)
                
    
        # if "\\x03" == button: 
            # self.stop()

    def start(self):
        self.kl.start()
        self.ml.start()
        super().start()  

    def stop(self):
        self.kl.stop()
        self.ml.stop()
        for function in self.call_stop_functions:
            function()
        super().stop()
        

    def act(self):
        super().act()
        for key in self.key_orders:
        
            if key == 'multi_clicks':
                for key_order in self.key_orders[key]:
                
                    last_clic = self.left_clicks_history[-1]
                    compare_clic = self.left_clicks_history[-1*key_order.get('number', 2)]
                    within = key_order.get('within', 0)
                    
                    if last_clic and compare_clic and within:
                        key_order['enabled'] = last_clic - compare_clic < within
                        if key_order['enabled']:
                            self.send_next_action(key_order)
                            self.reset_left_clicks_history()
                        
                continue
                
            if key not in self.history: continue
            for key_order in self.key_orders[key]:
            
                key_order['enabled'] =  self.now - self.history.get(key, self.now - 10) >= key_order.get('time_pressed', 0)\
                                        and key in self.history \
                                        and not self.is_on_cool_down(key_order)
                
                
                if key_order['enabled']:
                    self.send_next_action(key_order)
 
