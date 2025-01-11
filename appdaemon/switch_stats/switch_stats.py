import datetime
import re
import appdaemon.plugins.hass.hassapi as hass

class SwitchStats(hass.Hass): 

    def initialize(self):
 
        start_time = datetime.datetime.now() #datetime.time(0, 0, 0)
        interval = self.args["interval"]
        self.run_every(self.update_stats_cb, start_time, interval) 
        #self.run_minutely(self.update_stats_cb, start_time)
        self.update_stats_cb(None)

    def update_stats_cb(self, cb_args):
        ents = self.entities.switch 
        for ent in ents:  
          included = False
          for ie in self.args["include"]:
            if re.match(ie["entity_id"], ent):
              included = True
              break 
          if (included):
            self.update_entity_stats(ent)

    def update_entity_stats(self, entity):
        #self.log(entity)
        hist = self.get_history(entity_id = "switch." + entity, days = 7)
        state = 0
        v1d = 0
        v3d = 0
        v7d = 0         
        for rec in hist[0]:
            if (rec["last_changed"].find('.') > 0):
                last_changed = datetime.datetime.strptime(rec["last_changed"], "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                last_changed = datetime.datetime.strptime(rec["last_changed"], "%Y-%m-%dT%H:%M:%S%z")
            if (state == 0): #unknown state
                if (rec["state"] == 'off'):
                  state = 1 
                elif (rec["state"] == 'on'):
                  start_date = last_changed
                  state = 2 
            elif (state == 1): #turned off
                if (rec["state"] == 'off'):
                  state = 1 
                elif (rec["state"] == 'on'):
                  start_date = last_changed
                  state = 2 
                else:
                  state = 0 
            elif (state == 2): #turned on
                if (rec["state"] == 'off'):
                  delta = last_changed - start_date
                  dt_now = datetime.datetime.now(datetime.timezone.utc)
                  if (start_date >= dt_now - datetime.timedelta(days=1)):
                    v1d = v1d + delta.total_seconds()
                  if (start_date >= dt_now - datetime.timedelta(days=3)):
                    v3d = v3d + delta.total_seconds()
                  if (start_date >= dt_now - datetime.timedelta(days=7)):
                    v7d = v7d + delta.total_seconds()
                  state = 1
                elif (rec["state"] == 'on'):
                  state = 2 
                else:
                  state = 0            
             
        if (state == 2):
          delta = datetime.datetime.now(datetime.timezone.utc) - start_date
          v1d = v1d + delta.total_seconds()
          v3d = v3d + delta.total_seconds()
          v7d = v7d + delta.total_seconds()
          
        friendly_name = self.get_state("switch." + entity, attribute="friendly_name")
        self.set_state("sersor.stat_" + entity, state = round(v1d / 60, 0), attributes = {"friendly_name":friendly_name,"v1d": round(v1d / 60, 0),"v3d": round(v3d / 60, 0),"v7d": round(v7d / 60, 0) })
        self.log("sersor.stat_" + entity)

