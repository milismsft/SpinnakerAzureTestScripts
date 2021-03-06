#!/usr/bin/env python
import adal
import requests
import os
import json
from time import sleep, ctime
import sys

test_passed = True

authority = 'https://login.microsoftonline.com/' + os.environ['AZURE_TENANT_ID']
client_id = os.environ['AZURE_CLIENT_ID']
client_secret = os.environ['AZURE_APPKEY']
subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
clouddriver_host = 'http://localhost:7002'
azure_creds = os.environ['AZURE_CREDENTIALS']
if (azure_creds == ''):
 	azure_creds = 'azure-cred1'

token_response = adal.acquire_token_with_client_credentials(
	authority,
	client_id,
	client_secret
)

access_token = token_response.get('accessToken')
headers = {"Authorization": 'Bearer ' + access_token}

security_group_endpoint = 'https://management.azure.com/subscriptions/' + subscription_id + '/resourceGroups/azuresg1-westus/providers/Microsoft.Network/networkSecurityGroups/azuresg1-st1-d1?api-version=2015-05-01-preview'
deployment_endpoint = 'https://management.azure.com/subscriptions/' + subscription_id + '/resourceGroups/azuresg1-westus/providers/microsoft.resources/deployments/azuresg1-st1-d1-deployment?api-version=2015-11-01'

print ctime(), ' - Check for existing security group'
sys.stdout.flush()
r = requests.get(security_group_endpoint, headers=headers)

#the next line will fail if there is not 'error' as the first element.
#this should pass if the security group has not been created yet
if (not r.json()['error']):
	test_passed = False

#create a new securityGroup through clouddriver
url = clouddriver_host + '/ops'
sg_data = '[ { "upsertSecurityGroup": { "cloudProvider" : "azure", "appName" : "azuresg1", "securityGroupName" : "azuresg1-st1-d1", "stack" : "st1", "detail" : "d1", "credentials" : "' + azure_creds + '", "region" : "westus", "vnet" : "none", "tags" : { "appName" : "testazure4", "stack" : "sg22", "detail" : "d11"}, "securityRules" : [ { "name" : "rule1", "description" : "Allow FE Subnet", "access" : "Allow", "destinationAddressPrefix" : "*", "destinationPortRange" : "433", "direction" : "Inbound", "priority" : 100, "protocol" : "TCP", "sourceAddressPrefix" : "10.0.0.0/24", "sourcePortRange" : "*" } ], "name" : "azuresg1-st1-d1", "user" : "[anonymous]" }} ]'

print ctime(), ' - Post new security group'
sys.stdout.flush()
r = requests.post(url, data = sg_data, headers={'Content-Type': 'application/json'})
print ctime(), ' - result: ', (r.text)
sys.stdout.flush()

#continuously check the deployment until it is complete
def CheckDeployment():
	print ctime(), ' - Waiting for deployment...'
	sys.stdout.flush()
	r = requests.get(deployment_endpoint, headers=headers)
	while (r.text.find('error') != -1):
		sleep(10)
		r = requests.get(deployment_endpoint, headers=headers)
	
	provisioningState = 'none'
	
	print ctime(), ' - Checking deployment state'
	sys.stdout.flush()
	
	while (provisioningState != 'Succeeded'):
		sleep(10)
		r = requests.get(deployment_endpoint, headers=headers)
		provisioningState = r.json()['properties']['provisioningState']
		print ctime(), ' - provisioningState: ', provisioningState
		sys.stdout.flush()
		
	print ctime(), ' - Deployment complete'
	sys.stdout.flush()
#deployment complete

CheckDeployment()

#validate creation
print ctime(), ' - Validate Create'
sys.stdout.flush()
r = requests.get(security_group_endpoint, headers=headers)

if (r.json()['name'] == 'azuresg1-st1-d1'):
	print ctime(), ' - securityGroup Created'
	sys.stdout.flush()
else:
	print ctime(), ' - Create Failed'
	sys.stdout.flush()
	test_passed = False
#end creation validation

#update the securityGroup
url = clouddriver_host + '/ops'

sg_update = '[ { "upsertSecurityGroup": { "cloudProvider" : "azure", "appName" : "azuresg1", "securityGroupName" : "azuresg1-st1-d1", "stack" : "st1", "detail" : "d1", "credentials" : "' + azure_creds + '", "region" : "westus", "vnet" : "none", "tags" : { "appName" : "testazure4", "stack" : "sg22", "detail" : "d11"}, "securityRules" : [ { "name" : "rule1", "description" : "Allow FE Subnet", "access" : "Allow", "destinationAddressPrefix" : "*", "destinationPortRange" : "433", "direction" : "Inbound", "priority" : 100, "protocol" : "TCP", "sourceAddressPrefix" : "10.0.0.0/24", "sourcePortRange" : "*" }, { "name" : "rule2", "description" : "Block RDP", "access" : "Deny", "destinationAddressPrefix" : "*", "destinationPortRange" : "3389", "direction" : "Inbound", "priority" : 101, "protocol" : "TCP", "sourceAddressPrefix" : "Internet", "sourcePortRange" : "*" } ], "name" : "azuresg1-st1-d1", "user" : "[anonymous]" }} ]'

print ctime(), ' - Update security group'
sys.stdout.flush()
r = requests.post(url, data = sg_update, headers={'Content-Type': 'application/json'})
print ctime(), ' - result: ', (r.text)
sys.stdout.flush()
#end update

#continuously check the deployment until it is complete
CheckDeployment()
#deployment complete

#validate the update
print ctime(), ' - Validate Deployment'
sys.stdout.flush()
r = requests.get(security_group_endpoint, headers=headers)

if (r.json()['properties']['securityRules'][1]['name'] == 'rule2'):
	print ctime(), ' - securityGroup Created'
	sys.stdout.flush()
else:
	print ctime(), ' - Creation Failed: ', r.json()['properties']['securityRules'][1]['name']
	sys.stdout.flush()
	test_passed = False
#end update validation


#
# DELETE
#
#delete a securityGroup through clouddriver
url = clouddriver_host + '/ops'

sg_delete = '[ { "deleteSecurityGroup": { "cloudProvider" : "azure", "appName" : "azuresg1", "securityGroupName" : "azuresg1-st1-d1", "regions": ["westus"], "credentials": "' + azure_creds + '" }} ]'

print ctime(), ' - Delete security group'
sys.stdout.flush()
r = requests.post(url, data = sg_delete, headers={'Content-Type': 'application/json'})
print ctime(), ' - result: ', (r.text)
sys.stdout.flush()

#validate delete
sleep(10)
print ctime(), ' - Validate Delete'
sys.stdout.flush()
r = requests.get(security_group_endpoint, headers=headers)

if (not r.json()['error']):
	print ctime(), ' - Deletion Failed: ', r.text
	test_passed = False
else:
	sys.stdout.flush()
	print ctime(), ' - securityGroup Deleted'
	sys.stdout.flush()

#end delete validation
#
# DELETE
#

if (test_passed):
	print('SUCCESS!!')
else:
	print('FAILED')
