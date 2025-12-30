# Hydraulic Automated Testing Tool

The purpose of this tool is to provide an automated way to:
* Run multiple hydraulic motion commands.
* Record a time trace for each of the hydraulic motion commands.
* Calculate metrics on the each of the motions.

## Prerequisits

The following prerequsits exist:

* Ensure truck is running a 4.6 or newer software version
* Ensure that remote hydraulic commands can be exectued over SSH by executing the following command without any dialogue prompts or interruptions.   If executed correctly, the forks will be raised to a height of 650mm.  Replace `{IP ADDRESS}` with actual IP Address.
    ```
    ssh -J seegrid@{IP ADDRESS} seegrid@rcn "./trunk/bin/util/rcn/hydraulics-control-tuner -a lift -b -o -r -c 650 -c 0"
    ```

* Create a python environment with your favorite environment manager (script tested on Python 3.12).  Use the pip(3) _requirements.txt_ file in the script directory.


* Install script in appropriate location:
```
git clone git@gitea.dev.seegrid.com:respinosa/RunHydraulicCommands.git
```

## Instructions

>**WARNING**: Ensure enough height clearance.  Script has the potential to command the forks to raise to the max height.

Script tested and developed on a linux environment. 

**step 1**. Home vehicle
**step 2**. Create a directory with the following format. This is known as the working directory:

```
{Truck Name}_{RS1/CR1}_LOAD_{# lbs}_{YYYY_MM_DD}
```
Replace tokens with:
`{Truck Name}`: Truck name
`{RS1/CR1}`:  Truck type
`{# lbs}`: Load on forks
`{YYY_MM_DD}`: Date of test

Example:  `Rocky_RS1_LOAD_3500_2025_07_14`


**step 3**. CD into created folder.
Create YML file project file, _project.yml_.  Add the correct IP address. A _project_ file is a text file that defines all the axis motition in the order of execution as well as the post process functions to analyze the recorded servo trace data.  Sample _project.yml_ files can be found in the _SampleProjectFiles_ directory in the scipt root directory.  These must be named to _project.yml_ and store on the root level of the working directory.



Sample _project.yml_ file:
```
IPAddress: "###.###.###.###"
PassWordRequired: False
IsHardWired: False
StepPause_sec: 1

Tasks:

# Actual movement of forks
- Name: initialize.yml

- Name: RS1_LiftLargeStep.yml
  Repeat: 2

- Name: RS1_LiftSmallStep.yml
  Repeat: 2

- Name: RS1_TiltLargeStep.yml
  Repeat: 2

- Name: RS1_ReachLargeStep.yml
  Repeat: 2

- Name: RS1_SideshiftLargeStep.yml
  Repeat: 2 

- Name: RS1_SideshiftSmallStep.yml
  Repeat: 2   

# Post process functions

- Name: RS1_LiftLargeStepProcess.yml
- Name: RS1_LiftSmallStepProcess.yml
- Name: RS1_TiltLargeStepProcess.yml
- Name: RS1_ReachLargeStepProcess.yml
- Name: RS1_SideshiftLargeStepProcess.yml
- Name: RS1_SideshiftSmallStepProcess.yml
```

**step 4**.  Source python environment for this script.  
From within the working directory just created, run

```
python3 /{location of script}/RunHydraulicCommands/RunHydCommands.py
```

The automated motion should start within a minute and run for 20~40 minutes.

**step 5**.  If attaching to a ticket, CD up one level, archive and compress the directory by running:
```
tar -zcf {working directory name}.tar.gz {working directory name}
```
attach *tar.gz to ticket.


## Results
Within the working directory, the following artifacts will be generated:
* **ServoLogs**: Directory with individual *.csv file for each hydraulic motion
* **out.txt**: File with the overshoot result of each discrete motion.  Example:
```
[1751399219.988]  [TASK: RS1_LiftLargeStep.yml][NAME: LiftLargeStepPosDir_Overshoot][VAL:0.30 ]
[1751399250.299]  [TASK: RS1_LiftLargeStep.yml][NAME: LiftLargeStepNegDir_Overshoot][VAL:-1.95 ]
[1751399296.893]  [TASK: RS1_LiftLargeStep.yml][NAME: LiftLargeStepPosDir_Overshoot][VAL:0.93 ]
[1751399327.149]  [TASK: RS1_LiftLargeStep.yml][NAME: LiftLargeStepNegDir_Overshoot][VAL:-1.24 ]
```
* **post_out.txt**:  File with overshoot and calculated metrics of each motion
* **resutls.(csv| txt)**:  File with summary of metrics for each motion
```
                                           NAME           MEAN            MAX            MIN      STDV                           VAL
16         LiftLargeStepNegDir_CommandDelayTime           0.11           0.11           0.11      0.00                  [0.11, 0.11]
12                 LiftLargeStepNegDir_MaxVinst        -210.24        -210.07        -210.42      0.18    [-210.068572, -210.418795]
1                 LiftLargeStepNegDir_Overshoot          -1.59          -1.24          -1.95      0.35                [-1.95, -1.24]
19                 LiftLargeStepPosDir_MaxVinst         178.60         179.10         178.10      0.50        [179.09885, 178.09719]
0                 LiftLargeStepPosDir_Overshoot           0.61           0.93           0.30      0.32                   [0.3, 0.93]
26                 LiftSmallStepNegDir_MaxVinst         -37.53         -37.41         -37.65      0.12      [-37.651549, -37.406319]
3                 LiftSmallStepNegDir_Overshoot          -0.45          -0.21          -0.70      0.24                 [-0.7, -0.21]
2                  LiftSmallStepPosDirOvershoot           2.42           2.72           2.11      0.31                  [2.11, 2.72]
33                 LiftSmallStepPosDir_MaxVinst          47.82          48.43          47.20      0.61        [47.202191, 48.431342]
```


