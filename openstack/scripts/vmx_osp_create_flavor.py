#! /usr/bin/python
#Copyright (c) Juniper Networks, Inc., 2017-2024.
#All rights reserved.

import yaml
import xml
from xml.etree import cElementTree as ET
import sys
import json
import subprocess
import pprint
import netifaces as ni
import string
import uuid
import os
from signal import signal, SIGPIPE, SIG_DFL

def flavor_pin(name):
        global flv_pin_count
	global compute
	hypervisor_id = []
	flv_pin_count  += 1
        aggr_present = 0
	if compute != "none":
	    compute = ''.join(compute.split())
	    hypv_list =  compute.split(",")
	    hypv_data_json = subprocess.Popen(['openstack', 'hypervisor', 'list', '-f', 'json'], stdout=subprocess.PIPE).communicate()[0]
	    hypv_data = json.loads(str(hypv_data_json))
	    for hypv in hypv_list:
                for h in range(len(hypv_data)):
		    hypv_name = hypv_data[h]['Hypervisor Hostname']
		    if hypv in hypv_name:
                         hypervisor_id.append(hypv_data[h]['ID'])
	    hypervisor_id.sort()
	    AGGREGATE_NAME = '-'.join(str(x) for x in hypervisor_id)+'-group'
        else:
            AGGREGATE_NAME = 'global-group'

	aggregate_propery =  AGGREGATE_NAME+'pinned=true'
	openstack_flv_config.write('nova flavor-key  ' +  str(name) + ' set  aggregate_instance_extra_specs:' + str(aggregate_propery))
      	openstack_flv_config.write('\n')
	openstack_flv_config.write('nova flavor-key  ' +  str(name) + ' set hw:cpu_policy=dedicated')
      	openstack_flv_config.write('\n')
        if flv_pin_count == 1:

		aggr_data_json = subprocess.Popen(['openstack', 'aggregate', 'list', '-f', 'json', '-c', 'Name'], stdout=subprocess.PIPE).communicate()[0]
		aggr_data = json.loads(str(aggr_data_json))
		for agr in range(len(aggr_data)):
                	aggr_name = aggr_data[agr]['Name']
                	if aggr_name == AGGREGATE_NAME:
                	   	aggr_present = 1

		if aggr_present == 0:
			openstack_flv_config.write('nova aggregate-create ' + str(AGGREGATE_NAME)  )
			openstack_flv_config.write('\n')
			openstack_flv_config.write('nova aggregate-set-metadata ' + str(AGGREGATE_NAME) + ' ' + str(aggregate_propery))
			openstack_flv_config.write('\n')
                	if compute == "none":
				host_data_json = subprocess.Popen(['openstack', 'compute', 'service',  'list', '--service', 'nova-compute', '-f',  'json', '-c', 'Host'], stdout=subprocess.PIPE).communicate()[0]
				host_data = json.loads(str(host_data_json))
         			for hst in range(len(host_data)):
				        host = host_data[hst]['Host']
                			openstack_flv_config.write('nova aggregate-add-host  ' + str (AGGREGATE_NAME) + ' ' + str(host) )
                			openstack_flv_config.write('\n')
                	else :
                                compute_list = compute.split(",")
                                for comp in compute_list:
                                        openstack_flv_config.write('nova aggregate-add-host  ' + str (AGGREGATE_NAME) + ' ' + str(comp) )
                                        openstack_flv_config.write('\n')



class vmx_config:

    def vmx_handle_host_osp(self, value):
        global openstack_flv_config
        global compute
        global flv_pin_count
	global vpfe_cpu_pinning

        flv_pin_count = 0
        image_params = dict(value[0])
        print "\nOpenstack Flavor Creation\n"

	vpfe_cpu_pinning = False
	if 'cpu-pinning' in image_params and image_params['cpu-pinning'] == True:
		vpfe_cpu_pinning = True

        if 'compute' in image_params:
		compute = image_params['compute']
        else:
		compute = 'none'

	openstack_flv_config = open(openstack_path + 'vmx_osp_flavors.sh', 'w')


    def flavor_present(self, name):
        flavor_list_json = subprocess.Popen(['openstack', 'flavor', 'list', '-f', 'json', '-c', 'Name'], stdout=subprocess.PIPE).communicate()[0]
	flavor_list = json.loads(str(flavor_list_json))
        for flv in range(len(flavor_list)):
                flavor_name = flavor_list[flv]['Name']
                if flavor_name == name:
			return True
        return False

    def vmx_openstack_re_flavors(self, re_tmp_params):
        global openstack_flv_config

        RE_FLAVOR_NAME = re_tmp_params['flavor-name']
        if self.flavor_present(RE_FLAVOR_NAME) == False :
        	print "Generating Flavor for vRE"
        	openstack_flv_config.write('nova flavor-create --is-public true ' + RE_FLAVOR_NAME + ' auto ' + str(re_tmp_params['memory-mb']) + " 40 " + str(re_tmp_params['vcpus']))
        	openstack_flv_config.write('\n')
                if vpfe_cpu_pinning == True:
		    flavor_pin(RE_FLAVOR_NAME)
        else:
                print "Warning: Flavor with name ", RE_FLAVOR_NAME , "  already present\n"

    def vmx_handle_routing_engine_params_osp(self, value):
        re_tmp_params = {
               'vcpus':0,
               'memory-mb':0,
               're_num':0,
               'flavor-name':'null',
               'interfaces':{
                              'type':'null',
                              'ipaddr':'null'
               }
            }
        re_params = dict(value[0])
        re_tmp_params['vcpus'] = re_params['vcpus']
        re_tmp_params['memory-mb'] = re_params['memory-mb']
        re_tmp_params['flavor-name'] = re_params['re-flavor-name']
        self.vmx_openstack_re_flavors(re_tmp_params)


    def vmx_handle_forwarding_engine_params_osp(self, value):
        self.vmx_create_forwarding_engine_params(value)

    def vmx_openstack_pfe_flavors(self, vpfe_params):
        global openstack_flv_config

        PFE_FLAVOR_NAME = vpfe_params['flavor-name']
        if self.flavor_present(PFE_FLAVOR_NAME) == False :
        	print "Generating Flavor for vPFE"
                if (vpfe_params['vcpus'] < 3  ):
                        print >>sys.stderr, "Error! vCPU cannot be less than 3 for vPFE"
                        sys.exit(2)

                if ((vpfe_params['vcpus'] >= 7)  and  (vpfe_params['memory-mb'] < 12288) ):
                        print >>sys.stderr, "Error! Memory cannot be less than 12G for vPFE with more than 7 vCPU "
                        sys.exit(2)

		openstack_flv_config.write('nova flavor-create --is-public true ' + str(PFE_FLAVOR_NAME) + " auto " + str(vpfe_params['memory-mb']) + " 40 " + str(vpfe_params['vcpus']))
		openstack_flv_config.write('\n')

                if vpfe_cpu_pinning == True:
		   flavor_pin(PFE_FLAVOR_NAME)
	        openstack_flv_config.write('nova flavor-key  ' +  str(PFE_FLAVOR_NAME) + ' set hw:mem_page_size=2048\n')
        else:
                print "Warning: Flavor with name ", PFE_FLAVOR_NAME , "  already present\n"


    def vmx_create_forwarding_engine_params(self, value):
        global num_pfe_cores
        vpfe_params = {
               'vcpus':0,
               'memory-mb':0,
               'flavor_name':'null',
               'static_ip':0,
               'external_ip':'null',
               'interfaces':{
                              'type':'null',
                              'ipaddr':'null'
               }
            }
        pfe_params = dict(value[0])
        vpfe_params['vcpus']=pfe_params['vcpus']
        vpfe_params['memory-mb']=pfe_params['memory-mb']
        vpfe_params['flavor-name']=pfe_params['pfe-flavor-name']
        self.vmx_openstack_pfe_flavors(vpfe_params)
        return 0


#
# Top level config demux. Add new as needed.
#
vmx_config_handlers = {
        "HOST":               vmx_config.vmx_handle_host_osp,
        "CONTROL_PLANE":      vmx_config.vmx_handle_routing_engine_params_osp,
        "FORWARDING_PLANE":   vmx_config.vmx_handle_forwarding_engine_params_osp,
}

# Command line arg check
if len(sys.argv) <= 1:
    usage_str = "Usage: " + sys.argv[0] + "<vmx config filename>"
    print usage_str
    sys.exit(0)

openstack_path="./"

# Open the config file
stream = open(str(sys.argv[1]), 'r')

# Load the yaml into a dict
vmx_configs = yaml.safe_load_all(stream)

vmx_cfg_parse_result = vmx_config()

# Init globals
num_re_cores=0
num_pfe_cores=0
num_re=0

vpfe_image_model = ""
vpfe_data = {}

num_pfe_interfaces=0
vmx_device_type_virtio=False
vpfe_cpu_pinning=False
numa_list = list()

# Load iterator again since its already used above (python limitation)
stream = open(str(sys.argv[1]), 'r')
vmx_configs = yaml.safe_load_all(stream)

# Go over each key
for key in vmx_configs:
    vmx_config_handlers[key.keys()[0]](vmx_cfg_parse_result,key.values())

