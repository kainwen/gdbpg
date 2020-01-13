Postgres and GPDB GDB commands
=======================

GDB commands making debugging Postgres and Greenplum internals easier.
Currently this provides a single command 'pgprint' that understand the 'Node'
structures used internally, can can print them semi-intelligently.

Forked from PostgreSQL debugging tool found here:

https://github.com/tvondra/gdbpg


Usage
-----

Copy the `gdbpg.py` script somewhere, and load it from `gdb`:

    $ gdb ... 
    (gdb) source /...path.../gdbpg.py 

and then just use `pgprint` command to print variables from gdb console.
E.g. if `plan` is pointing to `(PlannedStmt *)`, you may do this:
    
    (gdb) pgprint plan

and you'll get something like this:

PlannedStmt [commandType=CMD_SELECT planGen=PLANGEN_PLANNER queryId=0 hasReturning=false hasModifyingCTE=false canSetTag=true transientPlan=false oneoffPlan=false
             simplyUpdatable=false dependsOnRole=false parallelModeNeeded=false numSlices=2 slices=0x56059fb60a08 subplan_sliceIds=0x56059fb61458 rewindPlanIDs=0x0
             nParamExec=0 query_mem=0 metricsQueryType=0 '\000']
	[planTree] 
		-> Motion [startup_cost=0 total_cost=2989 plan_rows=96300 plan_width=4 parallel_aware=false plan_node_id=0]
		          [motionType=MOTIONTYPE_GATHER sendSorted=false motionID=1 collations=0x0]
			[targetlist] 
				TargetEntry [resno=1 resname="a" resorigtbl=16392 resorigcol=1]
					Var [varno=OUTER_VAR varattno=1 vartype=23 varnoold=1 varoattno=1]
			[flow] Flow [flotype=FLOW_SINGLETON locustype=CdbLocusType_Entry segindex=-1 numsegments=3]
			[lefttree] 
				-> SeqScan [startup_cost=0 total_cost=1063 plan_rows=96300 plan_width=4 parallel_aware=false plan_node_id=1]
				           [scanrelid=1]
					[targetlist] 
						TargetEntry [resno=1 resname="a" resorigtbl=16392 resorigcol=1]
							Var [varno=1 varattno=1 vartype=23 varnoold=1 varoattno=1]
					[flow] Flow [flotype=FLOW_PARTITIONED locustype=CdbLocusType_Hashed segindex=0 numsegments=3]
	[rtable] 
		RangeTblEntry [rtekind=RTE_RELATION relid=16392 relkind='r' jointype=JOIN_INNER funcordinality=false ctelevelsup=0 self_reference=false forceDistRandom=false
		               lateral=false inFromCl=true requiredPerms=2 selectedCols=0x00000400]
	[relationOids] OidList: [16392]
