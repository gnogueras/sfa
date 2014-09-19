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
    
    def log_am_action(self, creds, action, parameters, options, config):
        log_msg="C-Lab Aggregate Manager \n" + "\tACTION: " + action + "\n"
        if parameters: log_msg += "\tPARAMETERS: " + str(parameters) + "\n"
        if options: log_msg += "\tOPTIONS: " + str(options) + "\n"
        if creds: 
            for credential in creds:
                user_urn = credential['geni_value'].split('<owner_urn>')[1].split('</owner_urn>')[0]
                log_msg += "\tBY USER: " + user_urn + "\n"
                log_msg += "\tAS C-LAB USER: " + config.SFA_CLAB_USER + "  IN GROUP: " + config.SFA_CLAB_GROUP + "\n\n"        
        self.info(log_msg)


clab_logger = ClabSfawrapLogger()