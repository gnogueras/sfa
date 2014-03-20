'''
Created on Mar 20, 2014

@author: gerard
'''

import logging

     
class ClabSfawrapLogger:
    def __init__ (self,logfile='/var/log/clab_sfawrap.log',loggername='clab_sfawrap',level=logging.DEBUG):
        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(level)
        
        handler_exists = False
        for existing_hdlr in self.logger.handlers:
            if existing_hdlr.baseFilename ==logfile and existing_hdlr.level==level:
                handler_exists = True
        if not handler_exists:     
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr = logging.FileHandler(logfile)
            hdlr.setFormatter(formatter)
            self.logger.addHandler(hdlr) 
        
    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)


clab_logger = ClabSfawrapLogger()