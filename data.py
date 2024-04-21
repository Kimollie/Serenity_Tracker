from filefifo import Filefifo
import time
from ssd1306 import SSD1306_I2C
import framebuf
from fifo import Fifo
from piotimer import Piometer

class Data:
    def __init__(self, adc_pin, sample_rate, oled):
        self.adc = Irs_ADC(adc_pin)
        self.sample_rate = sample_rate
        self.oled = oled
        self.count_sample = 1
        self.sample = 0

        self.count_display = 0
        self.mid_value = 65525/2
        self.avr = 0
        self.min_hr = 30
        self.max_hr = 200
        self.pre_peak_index = 0
        self.cur_peak_index = 0
        self.pre_peak = 0
        self.cur_peak = 0
        self.sum_sample = 0
        self.interval_num = 0
        self.ppi = 0
        self.sum_ppi = 0
        self.mean_ppi = 0
        self.mean_hr = 0
        self.ppi_list = []

    def read(self):
        self.tmr = Piometer(mode = Piometer.PERODIC, freq = self.sample_rate, callback = self.adc.handler)

    def stop_read(self):
        while self.adc.samples.has_data():
            self.adc.samples.get()
        self.tmr.deinit()

    def check_variability(self):
        return abs(int((self.cur_peak_index - self.pre_peak_index + 1) * 1000 / self.sample_rate ) - self.ppi) < 200
    def get_avr(self):
        self.sum_sample += self.sample
        self.avr = self.sum_sample / self.count_sample

    def hr_detect(self):
        if self.sample > (self.avr * 1.1):
            if self.sample > self.cur_peak:
                self.cur_peak = self.sample
                self.cur_peak_index = self.cur_peak_index
            else:
                if self.cur_peak > 0:
                    if (self.cur_peak_index - self.pre_peak_index) > (60 * self.sample_rate / self.min_hr):
                        self.pre_peak = 0
                        self.pre_peak_index = self.cur_peak_index
                    else:
                        if self.cur_peak >= (self.pre_peak * 0.8):
                            if self.pre_peak > 0:
                                if self.ppi != 0:
                                    if self.check_variability():
                                        self.interval_num = self.cur_peak_index - self.pre_peak_index
                                        self.ppi = round(self.interval_num * 1000 / self.sample_rate)
                                        self.ppi_list.append(self.ppi)
                                        print(round(60/ self.ppi * 1000))
                                else:
                                    self.interval_num = self.cur_peak_index - self.pre_peak_index
                                    self.ppi = round(self.interval_num * 1000 / self.sample_rate)
                            self.pre_peak = self.cur_peak
                            self.pre_peak_index = self.cur_peak_index
            self.cur_peak = 0
            
    def xal_mean_ppi (self):
        self.sum_ppi = 0
        for i in self.ppi_list:
            self.sum_ppi += i
        self.mean_hr = round(self.sum_ppi / len(self.ppi_list))
    
    def cal_mean_hr(self):
        self.mean_hr = round(60 /self.mean_ppi * 1000)
