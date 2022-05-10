# -*- coding: utf-8 -*-
import time
from threading import Thread
from pynput.keyboard import Controller as Keyboard
import datetime
import keyboard as KB
import logging 

   
class Act:
    
    keyboard = Keyboard()
    logger = logging.getLogger()
    
    def __init__(self):
        self.thread = Thread(target=self.thread_loop)
        self.running = False
        self.now = time.time()
        self.loop_frequency = 5
        self.retry_frequency = 5

    def start(self):
        self.running = True
        self.thread.start()

            
    def thread_loop(self):
        while self.running:
            self.thread_function()      
        
    def stop(self):
        self.running = False
        self.thread.join()  

    def request_send_key(self, key):
        return
        
    def request_color_position(self, color):
        return [0, 0]
        
    def request_permission(self):
        return True
        
    def thread_function(self):     
        if not self.request_permission(): 
            return time.sleep(self.retry_frequency)
        
        self.act()
        return time.sleep(self.loop_frequency)   
        
    def is_on_cool_down(self, order):
        return self.now - order.get('last_used', 0) < order.get('cool_down', 0)
    
    def send_next_action(self, order):
        if order.get('enabled', False) and order['actions']:

            if order.get('action_mode', 'all') == 'all':
                order['action'] = order['actions']
            else:
                last_action_i = order.get('last_action', -1) + 1
                if last_action_i > len(order['actions']) -1: last_action_i = 0
                order['action'] = order['actions'][last_action_i]
                order['last_action'] = last_action_i
                
                
            if order.get('action', None):
            
                self.press_key(order['action'])
                self.logger.info(f'{order.get("name", "Unknown")} triggered, sent "{order["action"]}"')
            
                order['last_used'] = self.now
                order['enabled'] = False
                
                
    def press_key(self, key):
        # Act.keyboard.type(key)
        KB.press_and_release(key)
        
    def act(self):
        self.now = time.time()
        return
        