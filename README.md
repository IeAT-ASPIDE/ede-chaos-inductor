# ede-chaos-inductor
Anomaly injection tool for Exascale systems developed during the H2020 ASPIDE Research Project.

## Events and Anomalies

Currently there are 9 anomaly types implemented. Most of the implemented anomalies are structured around hardware
related events. This is done in order to make the tool as versatile as possible. Software anomalies can be added by the end user.
The currently implemented anomalies are as follows:

* __Dummy__ - This anomaly does nothing, it is included only to mitigate the possibility and effects of detection bias.
* __CPU overload__ - Detects the number of CPU cores on any given node and saturates one or all CPU cores for a number of seconds (based on user set parameters).
* __Memory Eater__ - Writes data into the RAM of a compute node, the amount allocated is based on a user defined parameters: unit (KB, MB, GB), multi- plier, number of iterations. Thus simulating memory interference fault and saturation. User can also specify when the allocations are released.
* __Memory Leak__ - Similar to the memory eater except the allocations are never released (at least not during the execution of the application currently running) causing memory fragmentation.
* __Dial__ - Repeatedly executing large floating point calculations causing ALU interference.
* __DDot__ - Repeatedly calculates the dot product between two matrices. The size of each matrix is calculated based on CPU L2 cache size. Users can configure modifiers which are than used periodically to change matrix size to potential 10 times the cache size. The number of executions and time out can also be set by the user. The L2 cache size is automatically determined by each inductor agent at initialization. This simulates CPU cache fault.
* __Copy__ - Generates and then moves a large file from one location to another. Users can set: allocation unit (KB, MB, GB), multiplier, if the file should be removed or not and timeout between executions. This simulates I/O interference, I/O saturation or failing hard drive. Potentially degrading the I/O of any other application running on the same node. We should note that the generated file can also be moved from one compute node to another thus simulating network I/O interference.
* __Page fail__ - Makes any page allocation fail with a 50% probability. Simulating failing memory or misconfiguration.
* __IOError__ - Fails one out of 500 hard-drive I/O operations with a given proba- bility simulating I/O interference and failing hard-drives.
  
__NOTES:__ It should be noted that some anomalies (such as IOError) require additional kernel modules to be installed and configured. Also
some anomaly types perform in unexpected manner when used on virtualized hardware. This latter issue can be mitigated by 
configuration of anomalous instances by the end user.

## Workflow Generation and Scheduling

First users need to define a session where users can define a list of anomalies (and the parameters asociated with them). 
It is important to note that more than one anomaly can be executed at the same time. The following is an example session.

```json
{
	"anomalies":[
		{
			"type":"dummy",
			"options":{
				"stime":10
				},
			"prob":0.4
		},
		{
			"type":"cpu_overload",
			"options":{
				"half":1,
				"time_out":15
				},
			"prob":0.1
		},
		{
			"type":"memeater_v2",
			"options":{
				"unit":"gb",
				"multiplier":1,
				"iteration":2,
				"time_out":20
				},
			"prob":0.2
		},
		{
			"type":"copy",
			"options":{
				"unit":"kb",
				"multiplier":1,
				"remove":1,
				"time_out":20
				},
			"prob":0.2
		},
		{
			"type":"ddot",
			"options":{
				"iterations":1,
				"time_out":1,
				"modifiers":[0.9, 5, 2]
				},
			"prob":0.1
		}
	],
	"options":{
		"loop":1,
		"randomise":1,
		"sample_size":10,
		"distribution":"uniform"
	}
}
```

This is then used to generate a induction agent specific session. This looks as follows:

```json
{
	"<inducer_agent_id1>": {
		"anomalies": [
			{
				"type": "cpu_overload",
				"options": {
					"half": 1,
					"time_out": 15
				},
				"prob": 1.0
			}
		]
	},
	"<inducer_agent_id2>": {
		"anomalies": [
			{
				"type": "memeater_v2",
				"options": {
					"unit": "gb",
					"multiplier": 1,
					"iteration": 2,
					"time_out": 20
				},
				"prob": 0.5
			},
			{
				"type": "cpu_overload",
				"options": {
					"half": 1,
					"time_out": 15
				},
				"prob": 0.5
			}
		]
	},
	"options": {
		"randomise": 1,
		"sample_size": 10,
		"distribution": "uniform"
		}
}
```


## REST API

Each anomaly inductor agent has a REST API which can be accessed via whatever mechanism the end user deems appropriate.
We have an example command line tool however, we will list the REST API resources in full here.

```
GET http://<IP>:<Port>/node
```

Return compute node related information. Example output:

```json
{
	"disk": 499963170816,
	"machine": "x86_64",
	"memory": {
		"swap": 4294967296,
		"total": 17179869184
		},
	"node": "hal985m.local",
	"processor": {
		"cores_logical": 8,
		"cores_physical": 4,
		"frequency_current": 2700,
		"frequency_max": 2700,
		"frequency_min": 2700,
		"type": "i386"
		},
	"release": "18.7.0",
	"system": "Darwin",
	"version": "Darwin Kernel Version 18.7.0: Sat Oct 12 00:02:19 PDT 2019;", 
	"root":"xnu-4903.278.12~1/RELEASE_X86_64"
}
```

Get current session information:

```
GET http://<IP>:<Port>/chaos/session
```

Submitting user defined session decriptor as per the example found in the previouse section:

```
PUT http://<IP>:<Port>/chaos/session
```

Get the exact anomalies to be executed on node:
```
GET http://<IP>:<Port>/chaos/session/execute
```

Final session needs to be explicitly generated from the suer defined session descriptor. If before execution this is not 
done by the user before execution this will be implicitly done. In this scenario users will not have access before execution 
what anomalous events are schedueled on each node. This can be done using the following resource:

```
PUT http://<IP>:<Port>/chaos/session/execute
```

Execution of the final session is started using the resource bellow:

```
POST http://<IP>:<Port>/chaos/session/execute
```

Once execution has started it will return a descriptor which contains each scheduled anomaly and their unique job id:

```json
{
	"0373b6b6-ad5c-4f5b-a16d-ac29f0a4798a": {
		"anomaly": "dummy",
		"options": {
			"stime": 10
			}
	},
 	"1acc58a9-0baf-4a8b-b3c3-d36c5d662a95": {
		"anomaly": "cpu_overload",
		"options": {
			"half": 1,
			"time_out": 15
			}
	}
}
```

Fetching job id's can also be done using:

```
GET http://<IP>:<Port>/chaos/session/execute/jobs
```

This will return a descriptor of the form:

```json
{
	"jobs": {
		"started": [
			"2374c649-ec96-4a26-a273-a35172c4cc0c",
			"dae6fe4f-c47b-4877-be78-c25bf223b5a8",
			"9fbca075-1dfb-4751-ab93-b899efc833dd",
			"d6f8e2ec-5dbb-4244-88e4-2ff062a67795",
			"35cf653d-13fb-49c3-afed-17411f95c9ad",
			"36c8f740-e08d-4cf2-baf0-08a8fec75ac4"
			],
		"finished": [
			"9ff0f7bd-cebc-4c7d-802f-e8387ceafb43",
			"447559f8-700f-4152-a704-a2140df18874",
			"d3442b85-fb02-445d-9f57-df1d66501f85",
			"d0d00ec2-5b30-4632-86df-d3bfbec4555d"
			],
		"queued": [
			"78efbf00-88c6-4e8f-97a1-32e9fd0cee4a",
			"8299df3e-43fb-4c7c-9d66-4bc20b6358c2",
			"bcc580b2-d4dd-41a7-97e0-7b4217b77215"
			],
		"failed": [
			"077660a3-3700-4b4c-b0de-3676a4b5b8f3"
			]
	}
}
```

Stopping all jobs can be done using:

```
DELETE http://<IP>:<Port>/chaos/session/execute/jobs
```

To get information about specific jobs we can use:

```
GET http://<IP>:<Port>/chaos/session/execute/jobs/<job_id>
```

Deleting is done using the same resource:
```
DELETE http://<IP>:<Port>/chaos/session/execute/jobs/<job_id>
```

Each session execution will be logged. In order to see what logs are available we can use:

```
GET http://<IP>:<Port>/chaos/session/execute/jobs/logs
```

Downloading all logs can be done using:
```
POST http://<IP>:<Port>/chaos/session/execute/jobs/logs
```

Deleting logs can be done using:

```
DELETE http://<IP>:<Port>/chaos/session/execute/jobs/logs
```

Anomalies are schedueled on worker agents. There can be more than one worker per node. In order to fetch
worker status we can access:

```
GET http://<IP>:<Port>/workers
```

This will result in the following descriptor:

```json
{
	"workers": [
		{
			"id": "ff32c347f9c4437bb4039f2c8369c29f",
			"pid": 27486,
			"status": true
		}
	]
}
```

In order to start a new worker we must access:

```
POST http://<IP>:<Port>/workers
```

Deleteing workers can be done using:

```
DELETE http://<IP>:<Port>/workers
```

__NOTES:__ Non-idempontent requests have as a rule token based authentication. Thus unauthorized access to critical 
resources is protected.