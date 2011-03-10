import sys
import os
import os.path
import cgi
import urllib2
import logging
import random

from modules import storage
from modules.BeautifulSoup import BeautifulSoup
from rpc import client
from rpc.services import *

SITES_CFG = 'sites.xml'
QUOTA_PROPS = ['cpu_usage', 'outgoing_bandwidth', 'incomming_bandwidth', 'datastore']

QUOTA_LEVEL_RESERVE = 20.0
QUOTA_LEVEL_ALERT = 50.0

class TaskDispatcher(object):
    def __init__(self):
        loads = {}
        tasks = {}

        for s in storage.query(storage.SERVER):
            if s.servertype != 'extractor':
                continue

            # store the amount of mostly used resources
            max_load = 0.0
            for prop in QUOTA_PROPS:
                load = getattr(s, prop)
                max_load = load > max_load and load or max_load
                
            loads[s.address] = max_load

            # store the sites that the server is working on
            if not s.sites or s.sites == '':
                tasks[s.address] = []
            else:
                tasks[s.address] = s.sites.split(';')

        # estimate the value of load_per_site
        # if the current load level is low, use 3% per site
        total_load = sum(loads.values())
        total_sites = sum(len(s) for s in tasks.values())

        if total_sites > 0 and total_load > 10:
            avg_load_per_site = total_load / total_sites
        else:
            avg_load_per_site = 3.0

        self.loads = loads
        self.tasks = tasks
        self.avg_load_per_site = avg_load_per_site

    def balance_tasks(self):
        # The remote nature of servers make it extremely unreliable thus dangerous
        # to assign/remove tasks on servers. A failed remote call can result in duplicated
        # or missing tasks. As a tradeoff, we decided that we can tolerate duplicated
        # tasks on different servers, while make sure that there are no missing tasks
        # Then how to make sure of that? See RULE 1:
        # 
        # RULE 1: remove tasks only when there are duplicated tasks.
        #
        # For example, when we want to balance a task from server A to server B, we
        # first add the task on B's task list, but do not remove it on A. The next time,
        # we found the work is duplicated on two servers, we then remove it.
        #
        # Another difficulty when balancing tasks is that it's hard to estimate how the
        # load level will be after balancing. If a server is low in load level, and
        # we balance two tasks onto it. The next time the server could be over-loaded,
        # we need then balance the task off it. This will cause unnecessary costs. So
        # RULE 2 and 3 are introduced:
        #
        # RULE 2: only add/remove one task in each run
        # RULE 3: only consider balancing tasks to other servers when the load is high enough
        tasks = self.tasks
        loads = self.loads
        avg_load_per_site = self.avg_load_per_site

        # Is there any missing task?
        task = self.find_missing_task(tasks)
        if task:
            server = self.find_free_server(tasks, loads)
            if server:
                logging.info('TaskDispatcher: Adding task %s to server %s' % (task, server))
                self.add_task_to_server(server, task)
                return
            else:
                logging.warning('TaskDispatcher: Found missing task %s, but can not find a server to execute it' % task)

        # Is there any dup task?
        task, server = self.find_dup_task(tasks, loads)
        if task:
            logging.info('TaskDispatcher: Found dup task %s, remove it from server %s' % (task, server))
            self.remove_task_from_server(server, task)
            return

        # Is there any server that needs balancing?
        task, server = self.find_balancable_task(tasks, loads)
        if task:
            logging.info('TaskDispatcher: Found balancable task. Add task %s to server %s' % (task, server))
            self.add_task_to_server(server, task)
            return

    def find_missing_task(self, tasks):
        # Loads site list from config files
        # If there are missing tasks, we need first add them
        cfg = open(SITES_CFG, 'r')
        soup = BeautifulSoup(cfg)
    
        sites = []
        for node in soup.findAll('site'):
            sites.append(node.text)
        
        alltasks = set()
        for server in tasks:
            alltasks |= set(tasks[server])

        for site in sites:
            if site not in alltasks:
                return site

        return None

    def find_dup_task(self, tasks, loads):
        alltasks = {}
        for s in tasks:
            for task in tasks[s]:
                if task in alltasks:
                    # found a dup task, return the task and the server with larger load
                    s_other = alltasks[task]
                    return loads[s_other] > loads[s] and (task, s_other) or (task, s)
                else:
                    alltasks[task] = s

        return None, None
    
    def find_free_server(self, tasks, loads):
        server = None
        minsites = 500
        minload = 200.0

        for s in tasks:
            num_tasks = len(tasks[s])
            if num_tasks < minsites:
                server, minsites = s, num_tasks

        if loads[server] < QUOTA_LEVEL_ALERT:
            return server
        else:
            return None

    def find_balancable_task(self, tasks, loads):
        # if there are servers above alert level?
        maxload = -1.0
        server = None

        for s in loads:
            if loads[s] > maxload:
                server, maxload = s, loads[s]

        # if the maximum load level is below alert level, do nothing
        if maxload < QUOTA_LEVEL_ALERT:
            return None, None

        num_tasks = len(tasks[server])
        for s in loads:
            # reassign the work only if
            # 1. another server has two tasks less than the busy server
            # 2. the server's load is 20% than the busy server
            if loads[s] + 20 < maxload and \
               len(tasks[s]) + 2 < num_tasks:
                random_task = tasks[server][random.randint(0, num_tasks-1)]
                return random_task, s

        return None, None

    def add_task_to_server(self, server, task):
        client.call_remote(server, SITEUPDATER, 'add_task', task)

    def remove_task_from_server(self, server, task):
        client.call_remote(server, DATASTORE, 'remove', table=storage.SITE, siteid=task)

    
