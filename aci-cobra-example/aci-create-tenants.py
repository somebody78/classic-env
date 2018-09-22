#!<your-path-to-python>
#
# Script to create Tenants, VRF's, Bridge Domains, Application Profiles and EPGs
#
# ToDo's:
#
# Zuordnung Bridge Domain zu EPG schoen machen
#
#####################
# Imports
#####################
#
# list of packages that should be imported for this code to work
import readline
import re
import pdb
import cobra.mit.session
from cobra.mit.access import MoDirectory
from cobra.mit.request import ConfigRequest
from cobra.mit.request import TagsRequest

# Import model classes
from cobra.model.fvns import VlanInstP, EncapBlk
from cobra.model.infra import RsVlanNs
from cobra.model.fv import Tenant, Ctx, BD, RsCtx, Ap, AEPg, RsBd, RsDomAtt
from cobra.model.vmm import DomP, UsrAccP, CtrlrP, RsAcc

# disable SSL certificate error messages because APIC uses self-signed certificates
import requests
requests.packages.urllib3.disable_warnings()

######################################
# Classes
######################################
#
class MyAciObjects(object):
	'''
	A class representing an generic object
	'''
	# Class Attributes ##################
	# Methods #####################
	def __init__(self, name =  '', desc = ''):
		self.name = name
		self.desc = desc

	def __str__(self):
		return "Name ["+self.name+"], Description ["+self.desc+"]"

	def pretty_output(self, indent_level = 0, default_indent = '\t'):
		indent = indent_level * default_indent
		out_string = indent + "{:_<15}: {}\n".format("Name", self.name)
		out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
		return out_string

	def getType(self):
		''' Returns the Object's type as a string, should be overwritten in every child class '''
		return 'AciObjects'

	def setName(self, name):
		''' Sets Object's name to name '''
		self.name = name

	def getName(self):
		''' Returns the Object's name as a string '''
		return str(self.name)

	def setDesc(self, desc):
		''' Sets the Object's description to desc '''
		self.desc = desc

	def getDesc(self):
		''' Returns the Object's description as a string '''
		return str(self.desc)

	def getDefaultName(self, cust, index):
		''' Returns a Object's proposed default name as a string '''
		# return "{:_<10}_{:02d}".format(cust, index)
		return "{:_<10}_{:02d}".format(self.getType(), index)

	def getBasicData(self, project_desc, cust, index):
		name = collect_string_input('Name: ', 1, 14, default_value = self.getDefaultName(cust, index))
		desc = collect_string_input('Description: ', 1, 60, default_value = project_desc)
		self.setName(name)
		self.setDesc(self.getType() + ": " + desc)
	
# end of class MyAciObjects

class MyProject(object):
	'''
	A class representing project data
	'''
	# Attributes ##################
	cust = ''
	project = ''
	acct = ''
	desc = ''
	# Methods #####################
	def __init__(self, cust, project, acct):
		# print "A project is created ..."
		self.cust = cust
		self.project = project
		self.acct = acct

	def __str__(self):
		return "Project: Customer ["+self.cust+"], Project ["+self.project+"], Accounting ["+self.acct+"]"

	def __del__(self):
		print "Project ["+self.cust+"/"+self.project+"] is deleted!"

	def pretty_output(self, indent_level = 0, default_indent = '\t'):
		indent = indent_level * default_indent
		out_string = indent + "{:_<15}: {}\n".format("Customer Name", self.cust)
		out_string += indent + "{:_<15}: {}\n".format("Project", self.project)
		out_string += indent + "{:_<15}: {}\n".format("Accounting", self.acct)
		out_string += indent + "{:_<15}: {}\n".format("Description", self.getDesc())
		return out_string

	def setCust(self, cust):
		''' Sets the project's customer to cust '''
		self.cust = cust

	def getCust(self):
		''' Returns the project's customer as a string '''
		return str(self.cust)

	def setProject(self, proj):
		''' Sets the project's name to cust '''
		self.project = proj

	def getProject(self):
		''' Returns the project's name as a string '''
		return str(self.project)

	def setAcct(self, acct):
		''' Sets the project's accounting data to cust '''
		self.acct = acct

	def getAcct(self):
		''' Returns the project's acounting data as a string '''
		return str(self.acct)

	def getDesc(self):
		''' Returns the project's description as a string '''
		return "Cust: " + self.cust + ", Project: " + self.project + ", Acct: " + self.acct

# end of class MyProject

class MyTenant(MyAciObjects):
	'''
	A class representing a tenant
	'''
	# Class Attributes ##################

	# Methods #####################
	def __init__(self, name =  '', desc = ''):
		self.name = name
		self.desc = desc
		self.vrfs = []
		
	def getType(self):
		''' Returns the Object's type as a string, should be overwritten in every child class '''
		return 'Tenant'

	def pretty_output(self, indent_level = 0, default_indent = '\t'):
		indent = indent_level * default_indent
		out_string = indent + "{:_<15}: {}\n".format("Tenant Name", self.name)
		out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
		out_string += indent + "VRFs:" + "\n"
		for vrf in self.vrfs:
			out_string += vrf.pretty_output(indent_level+1) + "\n"
		return out_string
	
	def addVrf(self, vrf):
		''' Adds a VRF object to the list of attached VRF's '''
		self.vrfs.append(vrf)

	def getVrfs(self):
		''' Returns a list of VRF Objects '''
		return self.vrfs

# end of class MyTenant

class MyVrf(MyAciObjects):
	'''
	A class representing a VRF
	'''
	# Attributes ##################

	# Methods #####################
	def __init__(self, name =  '', desc = ''):
		self.name = name
		self.desc = desc
		self.bds = []
		self.aps = []

	def getType(self):
		''' Returns the Object's type as a string, should be overwritten in every child class '''
		return 'VRF'

	def pretty_output(self, indent_level = 0, default_indent = '\t'):
		indent = indent_level * default_indent
		out_string = indent + "{:_<15}: {}\n".format("VRF Name", self.name)
		out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
		out_string += indent + "BDs:" + "\n"
		for bd in self.bds:
			out_string += bd.pretty_output(indent_level+1) + "\n"
		for ap in self.aps:
			out_string += ap.pretty_output(indent_level+1) + "\n"
		return out_string

	def addBd(self, bd):
		''' Adds a BD object to the list of attached BD's '''
		self.bds.append(bd)

	def getBds(self):
		''' Returns a list of BD Objects '''
		return self.bds
		
	def getBdDict(self):
		''' Returns a dict of names of attached BDs. Key is an integer index. Optimized for function pick_value '''
		bd_dict = {}
		bd_index = 0
		for bd in self.bds:
			bd_index += 1
			bd_dict[str(bd_index)] = bd.getName()
		return bd_dict

	def addAppProfile(self, ap):
		''' Adds a VRF object to the list of attached VRF's '''
		self.aps.append(ap)

	def getAppProfiles(self):
		''' Returns a list of Application Profile Objects '''
		return self.aps

# end of class MyVrf

class MyBd(MyAciObjects):
	'''
	A class representing a BD, Bridge Domain
	'''
	# Attributes ##################
	# bds = [], is there something attached to a bridge domain?
	# Methods #####################
	def getType(self):
		''' Returns the Object's type as a string, should be overwritten in every child class '''
		return 'BD'


# end of class MyBd

class MyAppProfile(MyAciObjects):
	'''
	A class representing a Application Profile
	'''
	# Class Attributes ##################

	# Methods #####################
	def __init__(self, name =  '', desc = ''):
		self.name = name
		self.desc = desc
		self.epgs = []

	def getType(self):
		''' Returns the Object's type as a string, should be overwritten in every child class '''
		return 'AppProfile'

	def pretty_output(self, indent_level = 0, default_indent = '\t'):
		indent = indent_level * default_indent
		out_string = indent + "{:_<15}: {}\n".format("AppProfile Name", self.name)
		out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
		out_string += indent + "EPGs:" + "\n"
		for epg in self.epgs:
			out_string += epg.pretty_output(indent_level+1) + "\n"
		return out_string

	def addEpg(self, epg):
		''' Adds a EPG object to the list of attached EPG's '''
		self.epgs.append(epg)

	def getEpgs(self):
		''' Returns a list of EPG Objects '''
		return self.epgs

# end of class MyAppProfile

class MyEpg(MyAciObjects):
	'''
	A class representing an EPG, Endpoint Group
	'''
	# Attributes ##################

	# Methods #####################
	def __init__(self, name =  '', desc = ''):
		self.name = name
		self.desc = desc
		self.bd_name = ''

	def getType(self):
		''' Returns the Object's type as a string, should be overwritten in every child class '''
		return 'EPG'

	def setBdName(self, bd_name):
		''' Sets the EPG bd_name to bd_name '''
		self.bd_name = bd_name

	def getBdName(self):
		''' Returns the EPG bd_name as a string '''
		return str(self.bd_name)
	
	def pretty_output(self, indent_level = 0, default_indent = '\t'):
		indent = indent_level * default_indent
		out_string = indent + "{:_<15}: {}\n".format("EPG Name", self.name)
		out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
		out_string += indent + "{:_<15}: {}\n".format("Assoc. BD", self.bd_name)
		return out_string

# end of class MyEpg

######################################
# Functions
######################################
#
def welcome_screen():
    '''
    prints a nice welcome screen
    '''
    print "\n\n"
    print "###############################################"
    print "# Script to create a simple tenant in APIC."
    print "# A simple tenant consists of:"
    print "# - 1 context / VRF"
    print "# - 1 bridge domain"
    print "# - 1 application profile"
    print "# - 3 EPGs"
    print "#"
    print "# Attention"
    print "# Invalid characters will be removed automatically"
    print '# Valid characters are: "0-9, a-Z, _-:., "'
    print "#"
    print "###############################################"
    print "\n\n"

# end of function welcome_screen()

def replace_special_chars(old_string):
	'''
	Replaces all occurences of non-valid characters with _ an returns a new string
	'''
	return re.sub('[^a-zA-Z0-9 \:\.\_\-\,]', '', old_string)
	
# end of function replace_special_chars()

def collect_string_input(prompt, min_chars, max_chars, default_value = ''):
    '''
    Function to collect user input from the command line.
    The prompt will be displayed to asked for the input.
    Input will be treated as string and checked if the length in the range min_chars to max_chars.
    '''
    
    input = ''
    if default_value == '':
        while True:
            input1 = raw_input(prompt) or default_value
            input = replace_special_chars(input1.strip())
            if min_chars <= len(input) <= max_chars:
                break
            else:
                print "Sorry, input length should be in the range ["+str(min_chars)+","+str(max_chars)+"]"
                continue
    else:
        prompt = prompt + "[" + default_value + "]: "
        while True:
            input1 = raw_input(prompt) or default_value
            input = replace_special_chars(input1.strip())
            if min_chars <= len(input) <= max_chars:
                break
            else:
                print "Sorry, input length should be in the range ["+str(min_chars)+","+str(max_chars)+"]"
                continue
            
    return input
# end of function collect_string_input()

def pick_value(value_list, indent_level = 0, default_indent = '\t'):
	'''
	function to pick a value from a list.
	Input is a dictionary. A list of key, value lines is presented and the user is asked to type a key.
	Input is being tested if it is a valid key and the corresponding value is returned.
	'''
	indent = indent_level * default_indent
	while True:
		print "{}List of valid entries".format(indent)
		for (key, value) in value_list.iteritems():
			print "{}{}{:>10}: {}".format(indent, default_indent, key,value)
		
		selected_key = raw_input(indent + "Please enter a key: ").strip()
		if selected_key in value_list.keys():
			break
		else:
			print indent + "Sorry, input not valid!"
			
	print indent + "You've chosen [{}], value [{}]".format(selected_key, value_list[selected_key])
	return value_list[selected_key]

# end of function pick_value

######################################
# Variables
######################################
apic_1_URL = 'https://<your-apic-ip>'
apic_user = '<apic-user>'
apic_pw = '<apic-password>'

tenants = []			# list of tenants
tenant_index = 0		# index to keep track of number of tenants, basically for the default name
vrf_index = 0			# index to keep track of number of vrfs, basically for the default name
bd_index = 0			# index to keep track of number of bds, basically for the default name
max_items = 9			# number of maximum items. This is rather crude to give all items the same maximum. Just to make sure that the script is not running crazy
######################################
# Main program
######################################
# print opening screen
welcome_screen()

cust = collect_string_input('Customer ', 1, 10, default_value = 'Cust_1')
proj = collect_string_input('Project ', 1, 10, default_value = 'Project_1')
acct = collect_string_input('Project ', 1, 15, default_value = '12345678-ab.12')
project = MyProject(cust, proj, acct)
print str(project)

while True:
	print "\n\n"
	vrf_index = 0
	bd_index = 0
	ap_index = 0
	if tenant_index > max_items:
		print "Maximum number of items reached!"
		break
	get_inputs = collect_string_input("Create another Tenant [y/n]? ", 1, 1, default_value = 'y')
	if get_inputs != 'y':
		print "Okay, no more Tenants!"
		break
	# get tenant data
	tenant_index += 1
	tenant = MyTenant()
	tenant.getBasicData(project.getDesc(), project.cust, tenant_index)

	# get VRF data
	while True:
		if vrf_index > max_items:
			print "Maximum number of items reached!"
			break
		print "\n\n"
		get_inputs = collect_string_input("Create another VRF [y/n]? ", 1, 1, default_value = 'y')
		if get_inputs != 'y':
			print "Okay, no more VRFs!"
			break
		# get VRF data
		vrf_index += 1
		vrf = MyVrf()
		vrf.getBasicData(project.getDesc(), project.cust, vrf_index)

		# get bridge domain data
		while True:
			if bd_index > max_items:
				print "Maximum number of items reached!"
				break
			print "\n\n"
			get_inputs = collect_string_input("Create another BD [y/n]? ", 1, 1, default_value = 'y')
			if get_inputs != 'y':
				print "Okay, no more Bridge Domains!"
				break
			# get BD data
			bd_index += 1
			bd = MyBd()
			bd.getBasicData(project.getDesc(), project.cust, bd_index)
			# pdb.set_trace()
			vrf.addBd(bd)
		# end of while loop for BD data
		
		# get Application Profile data
		while True:
			if ap_index > max_items:
				print "Maximum number of items reached!"
				break
			print "\n\n"
			get_inputs = collect_string_input("Create another Application Profile [y/n]? ", 1, 1, default_value = 'y')
			if get_inputs != 'y':
				print "Okay, no more Application Profiles!"
				break
			# get AP data
			ap_index += 1
			ap = MyAppProfile()
			ap.getBasicData(project.getDesc(), project.cust, ap_index)
			
			# get epg data
			epg_index = 0
			while  True:
				if epg_index > max_items:
					print "Maximum number of items reached!"
					break
				print "\n\n"
				get_inputs = collect_string_input("Create another EPG [y/n]? ", 1, 1, default_value = 'y')
				if get_inputs != 'y':
					print "Okay, no more EPGs!"
					break
				# get EPG data
				epg_index += 1
				epg = MyEpg()
				epg.getBasicData(project.getDesc(), project.cust, epg_index)
				epg.bd_name = pick_value(vrf.getBdDict())
				# add EPG Object to VRF object
				ap.addEpg(epg)
			# end of while loop for epg data

			# add AP Object to VRF object
			vrf.addAppProfile(ap)
		# end of while loop for App Profile data
		
		# add VRF Object to Tenant object
		tenant.addVrf(vrf)
	# end of while loop for VRF data

	tenants.append(tenant)
# end of while loop for tenant data

print "You don't want to create another tenant? ..."

print "Project data:"
print project.pretty_output()
print "Tenant's data:"
for tenant in tenants:
	print tenant.pretty_output()

# commit this config to APIC?
print "Commit this config to APIC?"
get_inputs = collect_string_input("Commit this config to APIC [y/n]? ", 1, 1, default_value = 'y')

if get_inputs == 'y':
    # okay, let's do this
    # APIC login
    session = cobra.mit.session.LoginSession(apic_1_URL, apic_user, apic_pw, secure=False, timeout=180)
    md = MoDirectory(session)

    print "Trying to log in ..."
    md.login()
    print "Trying to log in ... successful"
    # Get the top level Policy Universe Directory
    uniMo = md.lookupByDn('uni')

    for tenant in tenants:
        print "Creating Tenant [{}]".format(tenant.getName())
        fvTenantMo = Tenant(uniMo, tenant.getName(), descr = tenant.getDesc())

        for vrf in tenant.getVrfs():
            print "Creating VRF [{}]".format(vrf.getName())
            Ctx(fvTenantMo, vrf.getName(), descr = vrf.getDesc())

            for bd in vrf.getBds():
                print "Creating BD [{}]".format(bd.getName())
                fvBDMo = BD(fvTenantMo, bd.getName(), descr = bd.getDesc())
                # Create association to VRF
                RsCtx(fvBDMo, tnFvCtxName=vrf.getName())

            for ap in vrf.getAppProfiles():
                print "Creating App Profile [{}]".format(ap.getName())
                fvApMo = Ap(fvTenantMo, ap.getName(), descr = ap.getDesc())
    
                for epg in ap.getEpgs():
                    print "Creating EPG [{}]".format(epg.getName())
                    fvAEPgMo = AEPg(fvApMo, epg.getName(), descr = epg.getDesc())
                    # Associate EPG to Bridge Domain
                    RsBd(fvAEPgMo, tnFvBDName=epg.getBdName())
                    # Associate EPG to VMM Domain
                    #RsDomAtt(fvAEPgMo, vmmDomPMo.dn)
                
        tenantCfg = ConfigRequest()
        tenantCfg.addMo(fvTenantMo)
        print "tenantCfg data: " + tenantCfg.data
        md.commit(tenantCfg)
    
    md.logout()
    
else:
    print "User cancelled the script! Good bye ..."

# end of main program