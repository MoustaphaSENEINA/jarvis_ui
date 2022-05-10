# -*- coding: utf-8 -*-
import time
from threading import Thread
import d3dshot
import json
import numpy as np
import act
import logging
    
class PixelAct(act.Act):
    
    index_pixel = [0, 1, 2]
    logger = logging.getLogger()
    
    def __init__(self, config):
        super().__init__()
        self.pixels_orders = config.get('pixelAct', [])
        self.run_pixels = config.get('run_pixels', [])
        self.stop_pixels = {}
        self.init_stop_pixels(config.get('stop_pixels', []))
        self.screen = d3dshot.create(capture_output="numpy")
        self.image = self.screen.screenshot()
        self.can_act = False
        self.is_acting = False
        self.loop_frequency = 0.2
        self.retry_frequency = 0.5
        
    
    def init_stop_pixels(self, pixels):
        for pixel in pixels:
            group = pixel.get('group_id', 'default')
            self.stop_pixels.setdefault(group, []).append(pixel)
    
    def thread_function(self):
        self.image = self.screen.screenshot()
        self.update_act_permission()
        super().thread_function()
            
    def update_act_permission(self):
    
        for groupe_name in self.stop_pixels:
            for pixel in self.stop_pixels[groupe_name]:
                if self.has_color_changed(pixel):
                    break
            else:
                if self.can_act: self.logger.info(f'In menus {groupe_name}')
                self.can_act = False
                return
        
        for pixel in self.run_pixels:
            if self.has_color_changed(pixel):
                self.logger.info('Not in App')
                time.sleep(2)
                self.can_act = False
                return
                
        self.can_act = True        

    def get_permission(self):
        return self.can_act
        
    def act(self):
        super().act()
        for order in self.pixels_orders:
            order['enabled'] = not self.is_on_cool_down(order) and \
                ((self.has_color_changed(order) and order.get('on_change', True)) or 
                (not self.has_color_changed(order) and not order.get('on_change', True)))
            if order['enabled']: self.send_next_action(order)

    def has_color_changed(self, pixel):
        x = pixel['x']
        y = pixel['y']
        color = pixel['color']
        current_color = self.image[y, x].tolist()
        
        self.logger.debug(f'{pixel["name"]}: {color} -> {current_color}')
        
        for i in PixelAct.index_pixel:
            if not (-20 <= color[i] - current_color[i] <= 20):
                return True
        return False
        
    def get_color_position(self, color):
        
        colors = [
            color,
            color,
            color,
        ]
        
        indices = np.any(np.all(self.image == color, axis=-1))
        try:
            y = indices[0].tolist()[0]
            x = indices[1].tolist()[0]
            return [y, x]
        except:
            return [None, None]
                