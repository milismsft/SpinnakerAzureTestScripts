#!/usr/bin/env python
import adal
import requests
import os
import json
from time import sleep, ctime
import sys

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

load_balancer_endpoint = 'https://management.azure.com/subscriptions/' + subscription_id + '/resourceGroups/azure1-westus/providers/Microsoft.Network/loadBalancers/azure1-st1-d1?api-version=2015-05-01-preview'
deployment_endpoint = 'https://management.azure.com/subscriptions/' + subscription_id + '/resourceGroups/azure1-westus/providers/microsoft.resources/deployments/azure1-st1-d1-deployment?api-version=2015-11-01'

#
# UPDATE
#
#update a new loadbalancer through clouddriver
url = clouddriver_host + '/ops'

lb_update = '[ { "upsertLoadBalancer": { "cloudProvider" : "azure", "appName" : "azure1", "loadBalancerName" : "azure1-st1-d1", "stack" : "st1", "detail" : "d1", "credentials" : "' + azure_creds + '", "region" : "West US", "vnet" : null, "probes" : [ { "probeName" : "healthcheck2", "probeProtocol" : "HTTP", "probePort" : 7001, "probePath" : "/healthcheck", "probeInterval" : 10, "unhealthyThreshold" : 2 } ], "securityGroups" : null, "loadBalancingRules" : [ { "ruleName" : "lbRule1", "protocol" : "TCP", "externalPort" : "80", "backendPort" : "80", "probeName" : "healthcheck2", "persistence" : "None", "idleTimeout" : "4" } ], "inboundNATRules" : [ { "ruleName" : "inboundRule1", "serviceType" : "SSH", "protocol" : "TCP", "port" : "80" } ], "name" : "azure1-st1-d1", "user" : "[anonymous]" }} ]'

print ctime(), ' - Update load balancer'
sys.stdout.flush()
r = requests.post(url, data = lb_update, headers={'Content-Type': 'application/json'})
print ctime(), ' - result: ', (r.text)
sys.stdout.flush()

#continuously check the deployment until it is complete
print ctime(), ' - Checking deployment state'
sys.stdout.flush()
provisioningState = 'none'

while (provisioningState != 'Succeeded'):
	sleep(10)
	r = requests.get(deployment_endpoint, headers=headers)
	provisioningState = r.json()['properties']['provisioningState']
	print ctime(), ' - provisioningState: ', provisioningState
	sys.stdout.flush()
	
print ctime(), ' - Deployment complete'
sys.stdout.flush()
#deployment complete

#validate update
print ctime(), ' - Validate Deployment'
sys.stdout.flush()
r = requests.get(load_balancer_endpoint, headers=headers)

if (r.json()['properties']['probes'][0]['name'] == 'healthcheck2'):
	print ctime(), ' - LoadBalancer Created'
	sys.stdout.flush()
else:
	print ctime(), ' - Creation Failed: ', r.json()['properties']['probes'][0]['name']
	sys.stdout.flush()
#end update validation
#
# UPDATE
#

print('SUCCESS!!')
