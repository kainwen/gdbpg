import gdb
import string

# TODO: Put these fields in a config file
PlanNodes = ['Result', 'Repeat', 'ModifyTable','Append', 'Sequence', 'Motion', 
        'AOCSScan', 'BitmapAnd', 'BitmapOr', 'Scan', 'SeqScan', 'TableScan',
        'IndexScan', 'DynamicIndexScan', 'BitmapIndexScan',
        'BitmapHeapScan', 'BitmapAppendOnlyScan', 'BitmapTableScan',
        'DynamicTableScan', 'TidScan', 'SubqueryScan', 'FunctionScan',
        'TableFunctionScan', 'ValuesScan', 'ExternalScan', 'AppendOnlyScan',
        'Join', 'NestLoop', 'MergeJoin', 'HashJoin', 'ShareInputScan',
        'Material', 'Sort', 'Agg', 'Window', 'Unique', 'Hash', 'SetOp',
                'Limit', 'DML', 'SplitUpdate', 'AssertOp', 'RowTrigger',
                'PartitionSelector' ]

# TODO: Put these fields in a config file
PathNodes = ['Path', 'AppendOnlyPath', 'AOCSPath', 'ExternalPath', 'PartitionSelectorPath',
             'IndexPath', 'BitmapHeapPath', 'BitmapAndPath', 'BitmapOrPath', 'TidPath',
             'CdbMotionPath', 'ForeignPath', 'AppendPath', 'MergeAppendPath', 'ResultPath',
             'HashPath', 'MergePath', 'MaterialPath', 'NestPath', 'JoinPath', 'UniquePath'] 

def format_plan_tree(tree, indent=0):
    'formats a plan (sub)tree, with custom indentation'

    # if the pointer is NULL, just return (null) string
    if (str(tree) == '0x0'):
        return '-> (NULL)'

    node_extra = ''
    if is_a(tree, 'Scan') or is_a(tree, 'SeqScan') or is_a(tree, 'TableScan') or is_a(tree, 'IndexScan') or is_a(tree, 'FunctionScan'):
        scan = cast(tree, 'Scan')
        node_extra += '<scanrelid=%(scanrelid)s' % {
            'scanrelid': scan['scanrelid'],
        }

        if is_a(tree, 'IndexScan'):
            indexscan = cast(tree, 'IndexScan')
            node_extra += ' indexid=%(indexid)s indexorderdir=%(indexorderdir)s' % {
                'indexid': indexscan['indexid'],
                'indexorderdir': indexscan['indexorderdir']
            }

        if is_a(tree, 'FunctionScan'):
            functionscan = cast(tree, 'FunctionScan')
            node_extra += ' funcordinality=%s' % functionscan['funcordinality']

        node_extra += '>'

    if is_a(tree, 'HashJoin') or is_a(tree, 'Join') or is_a(tree, 'NestLoop') or is_a(tree, 'MergeJoin'):
        join = cast(tree, 'Join')
        node_extra += '<jointype=%(jointype)s>' % {
            'jointype': join['jointype'],
        }

    if is_a(tree, 'Hash'):
        hash = cast(tree, 'Hash')
        node_extra += '<skewTable=%(skewTable)s skewColumn=%(skewColumn)s skewInherit=%(skewInherit)s>' %{
            'skewTable': hash['skewTable'],
            'skewColumn': hash['skewColumn'],
            'skewInherit': (int(hash['skewInherit']) == 1),
        }

    if is_a(tree, 'Sort'):
        sort = cast(tree, 'Sort')
        node_extra += '<numCols=%(numCols)s noduplicates=%(noduplicates)s share_type=%(share_type)s share_id=%(share_id)s driver_slice=%(driver_slice)s nsharer=%(nsharer)s nsharer_xslice=%(nsharer_xslice)s>' % {
            'numCols': sort['numCols'],
            'noduplicates': (int(sort['noduplicates']) == 1),
            'share_type': sort['share_type'],
            'share_id': sort['share_id'],
            'driver_slice': sort['driver_slice'],
            'nsharer': sort['nsharer'],
            'nsharer_xslice': sort['nsharer_xslice'],
        }

    if is_a(tree, 'Agg'):
        agg = cast(tree, 'Agg')
        node_extra += '<aggstrategy=%(aggstrategy)s numCols=%(numCols)s numGroups=%(numGroups)s aggParams=%(aggParams)s>' % {
            'aggstrategy': agg['aggstrategy'],
            'numCols': agg['numCols'],
            'numGroups': agg['numGroups'],
            'aggParams': format_bitmapset(agg['aggParams']),
        }

    if is_a(tree, 'SetOp'):
        setop = cast(tree, 'SetOp')
        node_extra += '<cmd=%(cmd)s strategy=%(strategy)s numCols=%(numCols)s flagColIdx=%(flagColIdx)s firstFlag=%(firstFlag)s numGroups=%(numGroups)s>' % {
            'cmd': setop['cmd'],
            'strategy': setop['strategy'],
            'numCols': setop['numCols'],
            'flagColIdx': setop['flagColIdx'],
            'firstFlag': setop['firstFlag'],
            'numGroups': setop['numGroups']
        }

    if is_a(tree, 'Motion'):
        motion= cast(tree, 'Motion')
        node_extra += '<motionType=%(motionType)s sendSorted=%(sendSorted)s motionID=%(motionID)s segidColIdx=%(segidColIdx)s nullsFirst=%(nullsFirst)s>' % {
            'motionType': motion['motionType'],
            'sendSorted': (int(motion['sendSorted']) == 1),
            'motionID': motion['motionID'],
            'segidColIdx': motion['segidColIdx'],
            'nullsFirst': motion['nullsFirst'],
        }



    retval = '''\n-> %(type)s (cost=%(startup).3f...%(total).3f rows=%(rows)s width=%(width)s) id=%(plan_node_id)s''' % {
        'type': format_type(tree['type']),    # type of the Node
        'node_extra': node_extra,
        'startup': float(tree['startup_cost']),    # startup cost
        'total': float(tree['total_cost']),    # total cost
        'rows': str(tree['plan_rows']),    # number of rows
        'width': str(tree['plan_width']),    # tuple width (no header)
        'plan_node_id': str(tree['plan_node_id']),
    }

    if node_extra != '':
        retval += add_indent(node_extra, 1, True)

    retval += format_optional_node_list(tree, 'targetlist')

    if is_a(tree, 'IndexScan'):
        retval += format_optional_node_list(tree, 'indexqual', 'IndexScan')

    # These are fields can be part of any node
    retval += format_optional_node_list(tree, 'initPlan')
    retval += format_optional_node_list(tree, 'qual')

    if is_a(tree, 'Result'):
        result = cast(tree, 'Result')
        if str(result['resconstantqual']) != '0x0':
            # Resconstant qual might be a list
            if is_a(result['resconstantqual'], 'List'):
                resconstantqual = cast(result['resconstantqual'], 'List')
            else:
                resconstantqual = result['resconstantqual']

            retval += add_indent('[resconstantqual]', 1, True)
            retval += '\n'
            retval += format_node(resconstantqual, 2)

    if is_a(tree, 'Motion'):
        motion = cast(tree, 'Motion')
        if str(motion['hashExprs']) != '0x0':
            numcols = int(motion['hashExprs']['length'])

            retval += add_indent('[hashExprs]', 1, True)

            hashfunctionoids = '[hashFunctionOids] ['
            for col in range(0,numcols):
                hashfunctionoids += '%d ' % motion['hashFuncs'][col]
            hashfunctionoids +=']'

            retval += add_indent(hashfunctionoids, 2, True)


    if is_a(tree, 'HashJoin') or is_a(tree, 'Join') or is_a(tree, 'NestLoop') or is_a(tree, 'MergeJoin'):
        # All join nodes can have this field
        retval += format_optional_node_list(tree, 'joinqual', 'Join')

        if is_a(tree, 'HashJoin'):
            retval += format_optional_node_list(tree, 'hashclauses', 'HashJoin')

    if is_a(tree, 'Sort'):
        append = cast(tree, 'Sort')
        numcols = int(append['numCols'])

        retval += add_indent('[sort indexes]', 1, True)

        index = ''
        for col in range(0,numcols):
            index += '[sortColIdx=%(sortColIdx)s sortOperator=%(sortOperator)s collation=%(collation)s, nullsFirst=%(nullsFirst)s]' % {
                'sortColIdx': append['sortColIdx'][col],
                'sortOperator': append['sortOperators'][col],
                'collation': append['collations'][col],
                'nullsFirst': append['nullsFirst'][col]
            }
            if col < numcols-1:
                index += '\n'

        retval += add_indent(index, 2, True)

    if is_a(tree, 'Agg'):
        agg = cast(tree, 'Agg')
        numcols = int(agg['numCols'])

        if (numcols >= 1):
            retval += add_indent('[operators]', 1, True)

            index = ''
            for col in range(0,numcols):
                index += '[grpColIdx=%(grpColIdx)s grpOperators=%(grpOperators)s]' % {
                    'grpColIdx': agg['grpColIdx'][col],
                    'grpOperators': agg['grpOperators'][col],
                }
                if col < numcols-1:
                    index += '\n'

            retval += add_indent(index, 2, True)

    if is_a(tree, 'SetOp'):
        setop = cast(tree, 'SetOp')
        numcols = int(setop['numCols'])

        retval += add_indent('[operators]', 1, True)

        index = ''
        for col in range(0,numcols):
            index += '[dupColIdx=%(dupColIdx)s dupOperator=%(dupOperator)s]' % {
                'dupColIdx': setop['dupColIdx'][col],
                'dupOperator': setop['dupOperators'][col],
            }
            if col < numcols-1:
                index += '\n'

        retval += add_indent(index, 2, True)

    if is_a(tree, 'FunctionScan'):
        retval += format_optional_node_list(tree, 'functions', 'FunctionScan')

    # format Append subplans
    if is_a(tree, 'Append'):
        append = cast(tree, 'Append')
        retval += '\n\t%s' % format_appendplan_list(append['appendplans'], 0)
    elif is_a(tree, 'SubqueryScan'):
        subquery = cast(tree, 'SubqueryScan')
        retval += '\n\t%s' % format_plan_tree(subquery['subplan'], 0)
    elif is_a(tree, 'ModifyTable'):
        modifytable= cast(tree, 'ModifyTable')
        retval += '\n\t%(plans)s' % format_appendplan_list(modifytable['plans'], 0)
    else:
        # format all the important fields (similarly to EXPLAIN)
        retval += '\n\t%s' % format_plan_tree(tree['lefttree'], 0)
        retval += '\n\t%s' % format_plan_tree(tree['righttree'], 0)

    return add_indent(retval, indent + 1)


def format_restrict_info(node, indent=0):
    retval = 'RestrictInfo [is_pushed_down=%(is_pushed_down)s can_join=%(can_join)s outerjoin_delayed=%(outerjoin_delayed)s]' % {
        'push_down': (int(node['is_pushed_down']) == 1),
        'can_join': (int(node['can_join']) == 1),
        'outerjoin_delayed': (int(node['outerjoin_delayed']) == 1)
    }
    retval += format_optional_node_field(node, 'clause', skip_tag=True)
    retval += format_optional_node_field(node, 'orclause', skip_tag=True)

    return add_indent(retval, indent)

def format_appendplan_list(lst, indent):
    retval = format_node_list(lst, indent, True)
    return add_indent(retval, indent + 1)

def format_alter_partition_cmd(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'AlterPartitionCmd (location=%(location)s)' % {
        'location': node['location']
    }

    retval += format_optional_node_field(node, 'partid')
    retval += format_optional_node_field(node, 'arg1')
    retval += format_optional_node_field(node, 'arg2')

    return add_indent(retval, indent)

def format_partition_cmd(node, indent=0):
    retval = 'PartitionCmd' % {
    }

    retval += format_optional_node_field(node, 'name')
    retval += format_optional_node_field(node, 'bound')

    return add_indent(retval, indent)

def format_alter_partition_id(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'AlterPartitionId (idtype=%(idtype)s location=%(location)s)' % {
        'idtype': node['idtype'],
        'location': node['location']
    }

    if (str(node['partiddef']) != '0x0'):
        if is_a(node['partiddef'], 'List'):
            partdef = '\n[partiddef]\n'
            partdef += add_indent('%s' % format_node_list(cast(node['partiddef'], 'List'), 0, True),1)
            retval += add_indent(partdef, 1)
        elif is_a(node['partiddef'], 'String'):
            partdef = '\n[partiddef]'
            partdef += add_indent('String: %s' % node['partiddef'], 1)
            retval += add_indent(partdef, 1)

    return add_indent(retval, indent)

def format_pg_part_rule(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PgPartRule (partIdStr=%(partIdStr)s isName=%(isName)s topRuleRank=%(topRuleRank)s relname=%(relname)s)' % {
        'partIdStr': node['partIdStr'],
        'isName': (int(node['isName']) == 1),
        'topRuleRank': node['topRuleRank'],
        'relname': node['relname']
    }

    retval += format_optional_node_field(node, 'pNode')
    retval += format_optional_node_field(node, 'topRule')

    return add_indent(retval, indent)

def format_partition_node(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionNode'


    retval += format_optional_node_field(node, 'part')
    retval += format_optional_node_field(node, 'default_part')
    retval += format_optional_node_list(node, 'rules')

    return add_indent(retval, indent)

def format_partition_elem(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionElem (partName=%(partName)s isDefault=%(isDefault)s AddPartDesc=%(AddPartDesc)s partno=%(partno)s rrand=%(rrand)s location=%(location)s)' % {
        'partName': node['partName'],
        'isDefault': (int(node['isDefault']) == 1),
        'AddPartDesc': node['AddPartDesc'],
        'partno': node['partno'],
        'rrand': node['rrand'],
        'location': node['location']
    }

    retval += format_optional_node_field(node, 'boundSpec')
    retval += format_optional_node_field(node, 'subSpec')
    retval += format_optional_node_field(node, 'storeAttr')
    retval += format_optional_node_list(node, 'colencs')

    return add_indent(retval, indent)

def format_index_elem(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'IndexElem [name=%(name)s indexcolname=%(indexcolname)s ordering=%(ordering)s nulls_ordering=%(nulls_ordering)s]' % {
        'name': getchars(node['name']),
        'indexcolname': getchars(node['indexcolname']),
        'ordering': node['ordering'],
        'nulls_ordering': node['nulls_ordering'],
    }

    retval += format_optional_node_field(node, 'expr')
    retval += format_optional_node_list(node, 'collation')
    retval += format_optional_node_field(node, 'opclass')

    return add_indent(retval, indent)

def format_path(node, indent=0):
    extra = ''
    retval = '%(type)s [pathtype=%(pathtype)s parent=%(parent)s rows=%(rows)s startup_cost=%(startup_cost)s total_cost=%(total_cost)s memory=%(memory)s motionHazard=%(motionHazard)s rescannable=%(rescannable)s sameslice_relids=%(sameslice_relids)s locus=%(locus)s' % {
        'type': format_type(node['type']),    # type of the Node
        'pathtype': node['pathtype'],
        'parent': node['parent'],
        'rows': node['rows'],
        'startup_cost': node['startup_cost'],
        'total_cost': node['total_cost'],
        'memory': node['memory'],
        'motionHazard': node['motionHazard'],
        'rescannable': node['rescannable'],
        'sameslice_relids': node['sameslice_relids'],
        'locus': node['locus'].address,
    }

    if is_a(node, 'JoinPath') or is_a(node, 'NestPath') or is_a(node, 'MergePath') or is_a(node, 'HashPath'):
        joinpath = cast(node, 'JoinPath')
        extra = ' jointype=%s' % (joinpath['jointype'])

    retval += '%s]' % (extra)


    retval += format_optional_node_field(node, 'parent')
    retval += format_optional_node_field(node, 'param_info')
    retval += format_optional_node_list(node, 'pathkeys', newLine=False)

    if is_a(node, 'JoinPath') or is_a(node, 'NestPath') or is_a(node, 'MergePath') or is_a(node, 'HashPath'):
        joinpath = cast(node, 'JoinPath')
        retval += format_optional_node_field(joinpath, 'outerjoinpath')
        retval += format_optional_node_field(joinpath, 'innerjoinpath')
        retval += format_optional_node_list(joinpath, 'joinrestrictinfo')

    if is_a(node, 'MaterialPath'):
        retval += format_optional_node_field(node, 'subpath', 'MaterialPath')

    if is_a(node, 'CdbMotionPath'):
        retval += format_optional_node_field(node, 'subpath', 'CdbMotionPath')

    if is_a(node, 'UniquePath'):
        retval += format_optional_node_field(node, 'subpath', 'UniquePath')

    return add_indent(retval, indent)

def format_partition_bound_spec(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionBoundSpec (pWithTnameStr=%(pWithTnameStr)s location=%(location)s)' % {
        'pWithTnameStr': node['pWithTnameStr'],
        'location': node['location'],
    }

    retval += format_optional_node_field(node, 'partStart')
    retval += format_optional_node_field(node, 'partEnd')
    retval += format_optional_node_field(node, 'partEvery')
    retval += format_optional_node_list(node, 'everyGenList', newLine=False)

    return add_indent(retval, indent)

def format_partition_values_spec(node, indent=0):
    retval = 'PartitionValuesSpec [location=%(location)s]' % {
        'location': node['location'],
    }

    retval += format_optional_node_list(node, 'partValues')

    return add_indent(retval, indent)

def format_partition_range_item(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionRangeItem (partedge=%(partedge)s everycount=%(everycount)s location=%(location)s)' % {
        'partedge': node['partedge'],
        'everycount': node['everycount'],
        'location': node['location'],
    }

    retval += format_optional_node_list(node, 'partRangeVal')

    return add_indent(retval, indent)

def format_partition(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'Partition [partid=%(partid)s parrelid=%(parrelid)s parkind=%(parkind)s parlevel=%(parlevel)s paristemplate=%(paristemplate)s parnatts=%(parnatts)s paratts=%(paratts)s parclass=%(parclass)s]' % {
        'partid': node['partid'],
        'parrelid': node['parrelid'],
        'parkind': node['parkind'],
        'parlevel': node['parlevel'],
        'paristemplate': (int(node['paristemplate']) == 1),
        'parnatts': node['parnatts'],
        'paratts': node['paratts'],
        'parclass': node['parclass']
    }

    return add_indent(retval, indent)

def format_cdb_process(node, indent=0):
    retval = 'CdbProcess [listenerAddr=%(listenerAddr)s listenerPort=%(listenerPort)s pid=%(pid)s contentid=%(contentid)s]' % {
        'listenerAddr': getchars(node['listenerAddr']),
        'listenerPort': node['listenerPort'],
        'pid': node['pid'],
        'contentid': node['contentid'],
    }

    return add_indent(retval, indent)

def format_def_elem(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'DefElem [defnamespace=%(defnamespace)s defname=%(defname)s defaction=%(defaction)s]' % {
        'defnamespace': node['defnamespace'],
        'defname': node['defname'],
        'defaction': node['defaction'],
    }

    retval += format_optional_node_field(node, 'arg')

    return add_indent(retval, indent)

def format_param(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'Param (paramkind=%(paramkind)s paramid=%(paramid)s paramtype=%(paramtype)s paramtypmod=%(paramtypmod)s location=%(location)s)' % {
        'paramkind': node['paramkind'],
        'paramid': node['paramid'],
        'paramtype': node['paramtype'],
        'paramtypmod': node['paramtypmod'],
        'location': node['location']
    }

    return add_indent(retval, indent)

def format_subplan(node, indent=0):
    retval = 'SubPlan [subLinkType=%(subLinkType)s plan_id=%(plan_id)s plan_name=%(plan_name)s]' % {
        'subLinkType': node['subLinkType'],
        'plan_id': node['plan_id'],
        'plan_name': node['plan_name'],
    }

    retval += format_optional_node_field(node, 'testexpr')
    retval += format_optional_node_list(node, 'paramids')
    retval += format_optional_node_list(node, 'args')

    return add_indent(retval, indent)


def format_partition_rule(node, indent=0):
    retval = '''PartitionRule (parruleid=%(parruleid)s paroid=%(paroid)s parchildrelid=%(parchildrelid)s parparentoid=%(parparentoid)s parisdefault=%(parisdefault)s parname=%(parname)s parruleord=%(parruleord)s partemplatespaceId=%(partemplatespaceId)s)''' % {
        'parruleid': node['parruleid'],
        'paroid': node['paroid'],
        'parchildrelid': node['parchildrelid'],
        'parparentoid': node['parparentoid'],
        'parisdefault': (int(node['parisdefault']) == 1),
        'parname': node['parname'],
        'parruleord': node['parruleord'],
        'partemplatespaceId': node['partemplatespaceId'],
    }
    if (str(node['parrangestart']) != '0x0'):
        retval += '\n\t[parrangestart parrangestartincl=%(parrangestartincl)s] %(parrangestart)s' % {
            'parrangestart': format_node_list(cast(node['parrangestart'], 'List'), 1, True),
            'parrangestartincl': (int(node['parrangestartincl']) == 1),
        }

    if (str(node['parrangeend']) != '0x0'):
        retval += '\n\t[parrangeend parrangeendincl=%(parrangeendincl)s] %(parrangeend)s' % {
            'parrangeend': format_node_list(cast(node['parrangeend'], 'List'), 0, True),
            'parrangeendincl': (int(node['parrangeendincl']) == 1),
        }

    retval += format_optional_node_list(node, 'parrangeevery')
    retval += format_optional_node_list(node, 'parlistvalues')
    retval += format_optional_node_list(node, 'parreloptions')
    retval += format_optional_node_field(node, 'children')

    return add_indent(retval, indent)

def format_type(t, indent=0):
    'strip the leading T_ from the node type tag'

    t = str(t)

    if t.startswith('T_'):
        t = t[2:]

    return add_indent(t, indent)


def format_oid_list(lst, indent=0):
    'format list containing Oid values directly (not warapped in Node)'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    try:
        item = lst['head']

        # walk the list until we reach the last item
        while str(item) != '0x0':

            # get item from the list and just grab 'oid_value as int'
            tlist.append(int(item['data']['oid_value']))

            # next item
            item = item['next']
    except:
        for col in range(0, lst['length']):
            element = lst['elements'][col]
            tlist.append(int(element['oid_value']))

    return add_indent(str(tlist), indent)


def format_node_list(lst, indent=0, newline=False):
    'format list containing Node values'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return add_indent('(NULL)', indent)

    # we'll collect the formatted items into a Python list
    tlist = []

    try:
        item = lst['head']

        # walk the list until we reach the last item
        while str(item) != '0x0':

            # we assume the list contains Node instances, so grab a reference
            # and cast it to (Node*)
            node = cast(item['data']['ptr_value'], 'Node')

            # append the formatted Node to the result list
            tlist.append(format_node(node))

            # next item
            item = item['next']
    except:
        for col in range(0, lst['length']):
            element = lst['elements'][col]
            node = cast(element['ptr_value'], 'Node')
            tlist.append(format_node(node))

    retval = str(tlist)
    if newline:
        retval = "\n".join([str(t) for t in tlist])

    return add_indent(retval, indent)


def format_char(value):
    '''convert the 'value' into a single-character string (ugly, maybe there's a better way'''

    str_val = str(value.cast(gdb.lookup_type('char')))

    # remove the quotes (start/end)
    return str_val.split(' ')[1][1:-1]


def format_bitmapset(bitmapset):
    if (str(bitmapset) == '0x0'):
        return '0x0'

    num_words = int(bitmapset['nwords'])
    retval = '0x'
    for word in reversed(range(num_words)):
        retval += '%08x' % int(bitmapset['words'][word])
    return retval


def format_node_array(array, start_idx, length, indent=0):

    items = []
    for i in range(start_idx, start_idx + length - 1):
        items.append(str(i) + " => " + format_node(array[i]))

    return add_indent(("\n".join(items)), indent)


def format_node(node, indent=0):
    'format a single Node instance (only selected Node types supported)'

    if str(node) == '0x0':
        return add_indent('(NULL)', indent)

    retval = ''
    type_str = str(node['type'])

    if is_a(node, 'SortGroupClause'):
        node = cast(node, 'SortGroupClause')

        retval = format_sort_group_clause(node)

    elif is_a(node, 'TableLikeClause'):
        node = cast(node, 'TableLikeClause')

        retval = format_table_like_clause(node)

    elif is_a(node, 'Const'):
        node = cast(node, 'Const')

        retval = format_const(node)

    elif is_a(node, 'Aggref'):
        node = cast(node, 'Aggref')

        retval = format_aggref(node)

    elif is_a(node, 'A_Expr'):
        node = cast(node, 'A_Expr')

        retval = format_a_expr(node)

    elif is_a(node, 'A_Const'):
        node = cast(node, 'A_Const')

        retval = format_a_const(node)

    elif is_a(node, 'CoalesceExpr'):
        node = cast(node, 'CoalesceExpr')

        retval = format_coalesce_expr(node)

    elif is_a(node, 'RelOptInfo'):
        node = cast(node, 'RelOptInfo')

        retval = format_reloptinfo(node)

    elif is_a(node, 'GenericExprState'):
        node = cast(node, 'GenericExprState')

        retval = format_generic_expr_state(node)

    elif is_a(node, 'PlannerInfo'):
        retval = format_planner_info(node)

    elif is_a(node, 'List'):
        node = cast(node, 'List')

        retval = format_node_list(node, 0, True)

    elif is_a(node, 'Plan'):
        retval = format_plan_tree(node)

    elif is_a(node, 'RestrictInfo'):
        node = cast(node, 'RestrictInfo')

        retval = format_restrict_info(node)

    elif is_a(node, 'FuncExpr'):
        node = cast(node, 'FuncExpr')

        retval = format_func_expr(node)

    elif is_a(node, 'RelabelType'):
        node = cast(node, 'RelabelType')

        retval = format_relabel_type(node)

    elif is_a(node, 'CoerceViaIO'):
        node = cast(node, 'CoerceViaIO')

        retval = format_coerce_via_io(node)

    elif is_a(node, 'ScalarArrayOpExpr'):
        node = cast(node, 'ScalarArrayOpExpr')

        retval = format_scalar_array_op_expr(node)

    elif is_a(node, 'BoolExpr'):
        node = cast(node, 'BoolExpr')

        retval = format_bool_expr(node)

    elif is_a(node, 'SubLink'):
        node = cast(node, 'SubLink')

        retval = format_sublink(node)

    elif is_a(node, 'AlterPartitionCmd'):
        node = cast(node, 'AlterPartitionCmd')

        retval = format_alter_partition_cmd(node)

    elif is_a(node, 'PartitionCmd'):
        node = cast(node, 'PartitionCmd')

        retval = format_partition_cmd(node)

    elif is_a(node, 'AlterPartitionId'):
        node = cast(node, 'AlterPartitionId')

        retval = format_alter_partition_id(node)

    elif is_a(node, 'PgPartRule'):
        node = cast(node, 'PgPartRule')

        retval = format_pg_part_rule(node)

    elif is_a(node, 'PartitionNode'):
        node = cast(node, 'PartitionNode')

        retval = format_partition_node(node)

    elif is_a(node, 'PartitionElem'):
        node = cast(node, 'PartitionElem')

        retval = format_partition_elem(node)

    elif is_a(node, 'IndexElem'):
        node = cast(node, 'IndexElem')

        retval = format_index_elem(node)

    elif is_a(node, 'Path'):
        node = cast(node, 'Path')

        retval = format_path(node)

    elif is_a(node, 'PartitionBoundSpec'):
        node = cast(node, 'PartitionBoundSpec')

        retval = format_partition_bound_spec(node)

    elif is_a(node, 'PartitionValuesSpec'):
        node = cast(node, 'PartitionValuesSpec')

        retval = format_partition_values_spec(node)

    elif is_a(node, 'PartitionRangeItem'):
        node = cast(node, 'PartitionRangeItem')

        retval = format_partition_range_item(node)

    elif is_a(node, 'Partition'):
        node = cast(node, 'Partition')

        retval = format_partition(node)

    elif is_a(node, 'PartitionBy'):
        node = cast(node, 'PartitionBy')

        retval = format_partition_by(node)

    elif is_a(node, 'PartitionSpec'):
        node = cast(node, 'PartitionSpec')

        retval = format_partition_spec(node)

    elif is_a(node, 'DefElem'):
        node = cast(node, 'DefElem')

        retval = format_def_elem(node)

    elif is_a(node, 'Param'):
        node = cast(node, 'Param')

        retval = format_param(node)

    elif is_a(node, 'String'):
        node = cast(node, 'Value')

        retval = 'String [%s]' % getchars(node['val']['str'])

    elif is_a(node, 'Integer'):
        node = cast(node, 'Value')

        retval = 'Integer [%s]' % node['val']['ival']

    elif is_a(node, 'SubPlan'):
        node = cast(node, 'SubPlan')

        retval = format_subplan(node)

    elif is_a(node, 'PartitionRule'):
        node = cast(node, 'PartitionRule')

        retval = format_partition_rule(node)

    elif is_a(node, 'CdbProcess'):
        node = cast(node, 'CdbProcess')

        retval = format_cdb_process(node)

    elif is_a(node, 'OidList'):
        retval = 'OidList: %s' % format_oid_list(node)

    elif is_a(node, 'IntList'):
        retval = 'IntList: %s' % format_oid_list(node)

    elif is_pathnode(node):
        node = cast(node, 'Path')

        retval = format_path(node)

    elif is_plannode(node):
        node = cast(node, 'Plan')

        retval = format_plan_tree(node)

    # TODO: NodeFormatter exceptions in these nodes
    elif is_a(node, "ColumnRef"):
        retval = format_type(type_str)

    else:
        node_formatter = NodeFormatter(node)
        retval += node_formatter.format()

    return add_indent(str(retval), indent)

def is_pathnode(node):
    for nodestring in PathNodes:
        #print "testing %s against %s" % (nodestring, node.address)
        if is_a(node, nodestring):
            return True

    return False

def is_plannode(node):
    for nodestring in PlanNodes:
        if is_a(node, nodestring):
            return True

    return False

def format_planner_info(info, indent=0):

    # Query *parse;			/* the Query being planned */
    # *glob;				/* global info for current planner run */
    # Index	query_level;	/* 1 at the outermost Query */
    # struct PlannerInfo *parent_root;	/* NULL at outermost Query */
    # List	   *plan_params;	/* list of PlannerParamItems, see below */

    retval = '''rel:
%(rel)s
rte:
%(rte)s
''' % {
        'rel':
        format_node_array(info['simple_rel_array'], 1,
                          int(info['simple_rel_array_size'])),
        'rte':
        format_node_array(info['simple_rte_array'], 1,
                          int(info['simple_rel_array_size']))
    }

    return add_indent(retval, indent)

def format_partition_by(node, indent=0):
    retval = 'PartitionBy [partType=%(partType)s partDepth=%(partDepth)s bKeepMe=%(bKeepMe)s partQuiet=%(partQuiet)s location=%(location)s]' % {
        'partType': node['partType'],
        'partDepth': node['partDepth'],
        'bKeepMe': (int(node['bKeepMe']) == 1),
        'partQuiet': node['partQuiet'],
        'location': node['location'],
    }

    retval += format_optional_node_field(node, 'keys')
    retval += format_optional_node_field(node, 'keyopclass')
    retval += format_optional_node_field(node, 'subPart')
    retval += format_optional_node_field(node, 'partSpec')
    retval += format_optional_node_field(node, 'partDefault')
    retval += format_optional_node_field(node, 'parentRel')

    return add_indent(retval, indent)

def format_partition_spec(node, indent=0):
    retval = 'PartitionSpec [istemplate=%(istemplate)s location=%(location)s]' % {
        'istemplate': node['istemplate'],
        'location': node['location'],
    }

    retval += format_optional_node_list(node, 'partElem')
    retval += format_optional_node_list(node, 'enc_clauses', newLine=False)
    retval += format_optional_node_field(node, 'subSpec')

    return add_indent(retval, indent)

def format_reloptinfo(node, indent=0):
    retval = 'RelOptInfo (kind=%(kind)s relids=%(relids)s rtekind=%(rtekind)s relid=%(relid)s rows=%(rows)s width=%(width)s)' % {
        'kind': node['reloptkind'],
        'rows': node['rows'],
        'width': node['width'],
        'relid': node['relid'],
        'relids': format_bitmapset(node['relids']),
        'rtekind': node['rtekind'],
    }

    return add_indent(retval, indent)

def format_generic_expr_state(node, indent=0):
    exprstate = node['xprstate']
    child = cast(node['arg'], 'ExprState')
    return '''GenericExprState [evalFunc=%(evalFunc)s childEvalFunc= %(childEvalFunc)s]
\t%(expr)s''' % {
#\tChild Expr:
#%(childexpr)s''' % {
            'expr': format_node(exprstate['expr']),
            'evalFunc': format_node(exprstate['evalfunc']),
            'childexpr': format_node(child['expr']),
            'childEvalFunc': child['evalfunc']
    }

def format_func_expr(node, indent=0):

    retval = """FuncExpr [funcid=%(funcid)s funcresulttype=%(funcresulttype)s funcretset=%(funcretset)s funcformat=%(funcformat)s""" % {
        'funcid': node['funcid'],
        'funcresulttype': node['funcresulttype'],
        'funcretset': (int(node['funcretset']) == 1),
        'funcvaridaic': (int(node['funcvariadic']) == 1),
        'funcformat': node['funcformat'],
    }

    if node['funccollid'] != 0:
        retval += ' funccollid=%s' % node['funccollid']
    if node['inputcollid'] != 0:
        retval += ' inputcollid=%s' % node['inputcollid']

    retval += ' location=%(location)s]' % {
        'location': node['location'],
    }

    retval += format_optional_node_list(node, 'args', skip_tag=True)

    return add_indent(retval, indent)

def format_relabel_type(node, indent=0):

    retval = """RelabelType [resulttype=%(resulttype)s resulttypmod=%(resulttypmod)s""" % {
        'resulttype': node['resulttype'],
        'resulttypmod': node['resulttypmod'],
    }

    if node['resultcollid'] != 0:
        retval += ' resultcollid=%s' % node['resultcollid']

    retval += ' relabelformat=%(relabelformat)s]' % {
        'relabelformat': node['relabelformat'],
    }

    retval += format_optional_node_field(node, 'arg', skip_tag=True)

    return add_indent(retval, indent)

def format_coerce_via_io(node, indent=0):

    retval = """CoerceViaIO [resulttype=%(resulttype)s coerceformat=%(coerceformat)s location=%(location)s""" % {
        'resulttype': node['resulttype'],
        'coerceformat': node['coerceformat'],
        'location': node['location'],
    }

    if node['resultcollid'] != 0:
        retval += ' resultcollid=%s' % node['resultcollid']

    retval += ']'

    retval += format_optional_node_field(node, 'arg', skip_tag=True)

    return add_indent(retval, indent)

def format_scalar_array_op_expr(node, indent=0):
    retval = """ScalarArrayOpExpr [opno=%(opno)s opfuncid=%(opfuncid)s useOr=%(useOr)s]
%(clauses)s""" % {
        'opno': node['opno'],
        'opfuncid': node['opfuncid'],
        'useOr': (int(node['useOr']) == 1),
        'clauses': format_node_list(node['args'], 1, True)
    }
    return add_indent(retval, indent)

def format_a_expr(node, indent=0):
    retval = "A_Expr [kind=%(kind)s location=%(location)s]" % {
        'kind': node['kind'],
        'location': node['location'],
        }

    retval += format_optional_node_list(node, 'name', newLine=False)
    retval += format_optional_node_field(node, 'lexpr')
    retval += format_optional_node_field(node, 'rexpr')

    return add_indent(retval, indent)

def format_a_const(node, indent=0):
    retval = "A_Const [val=(%(val)s) location=%(location)s]" % {
        'val': format_node(node['val'].address),
        'location': node['location'],
        }

    return add_indent(retval, indent)

def format_coalesce_expr(node, indent=0):
    retval = "CoalesceExpr [coalescetype=%(coalescetype)s location=%(location)s]" % {
        'coalescetype': node['coalescetype'],
        'location': node['location'],
        }

    retval += format_optional_node_list(node, 'args')

    return add_indent(retval, indent)

def format_bool_expr(node, indent=0):

    retval = 'BoolExpr [op=%s]' % node['boolop']
    retval += format_optional_node_list(node, 'args', skip_tag=True)

    return add_indent(retval, indent)

def format_sublink(node, indent=0):
    retval = """SubLink [subLinkType=%(subLinkType)s location=%(location)s]""" % {
        'subLinkType': node['subLinkType'],
        'location': (int(node['location']) == 1),
    }

    retval += format_optional_node_field(node, 'testexpr')
    retval += format_optional_node_list(node, 'operName')
    retval += format_optional_node_field(node, 'subselect')

    return add_indent(retval, indent)

def format_sort_group_clause(node, indent=0):
    retval = 'SortGroupClause [tleSortGroupRef=%(tleSortGroupRef)s eqop=%(eqop)s sortop=%(sortop)s nulls_first=%(nulls_first)s hashable=%(hashable)s]' % {
        'tleSortGroupRef': node['tleSortGroupRef'],
        'eqop': node['eqop'],
        'sortop': node['sortop'],
        'nulls_first': (int(node['nulls_first']) == 1),
        'hashable': (int(node['hashable']) == 1),
    }

    return add_indent(retval, indent)

def format_table_like_clause(node):
    retval = "TableLikeClause [options=%08x]" % int(node['options'])

    retval += format_optional_node_field(node, 'relation')

    return retval

def format_const(node, indent=0):
    retval = "Const [consttype=%s" % node['consttype']
    if (str(node['consttypmod']) != '0x0'):
        retval += " consttypmod=%s" % node['consttypmod']

    if node['constcollid']:
        retval += " constcollid=%s" % node['constcollid']

    retval += " constlen=%s constvalue=" % node['constlen']

    # Print the value if the type is int4 (23)
    if(int(node['consttype']) == 23):
        retval += "%s" % node['constvalue']
    # Print the value if type is oid
    elif(int(node['consttype']) == 26):
        retval += "%s" % node['constvalue']
    else:
        retval += "%s" % hex(int(node['constvalue']))

    retval += " constisnull=%(constisnull)s constbyval=%(constbyval)s" % {
            'constisnull': (int(node['constisnull']) == 1),
            'constbyval': (int(node['constbyval']) == 1) }

    retval += ']'

    return add_indent(retval, indent)

def format_aggref(node, indent=0):
    retval = '''Aggref (aggfnoid=%(fnoid)s aggtype=%(aggtype)s''' % {
        'fnoid': node['aggfnoid'],
        'aggtype': node['aggtype'],
    }

    if node['aggcollid'] != 0:
        retval += ' aggcollid=%s' % node['aggcollid']

    if node['inputcollid'] != 0:
        retval += ' inputcollid=%s' % node['inputcollid']

    retval += ''' aggtranstype=%(aggtranstype)s aggstar=%(aggstar)s aggvariadic=%(aggvariadic)s aggkind='%(aggkind)s' agglevelsup=%(agglevelsup)s aggsplit=%(aggsplit)s location=%(location)s)''' % {
        'aggtranstype': node['aggtranstype'],
        'aggstar': (int(node['aggstar']) == 1),
        'aggvariadic': (int(node['aggvariadic']) == 1),
        'aggkind': format_char(node['aggkind']),
        'agglevelsup': node['agglevelsup'],
        'aggsplit': node['aggsplit'],
        'location': node['location'],
    }

    retval += format_optional_node_list(node, 'args', skip_tag=True)
    retval += format_oid_list(node['aggargtypes'])
    retval += format_optional_node_list(node, 'aggdirectargs')
    retval += format_optional_node_list(node, 'aggorder')
    retval += format_optional_node_list(node, 'aggdistinct')
    retval += format_optional_node_field(node, 'aggfilter')
    return add_indent(retval, indent)

def is_a(n, t):
    '''checks that the node has type 't' (just like IsA() macro)'''

    if not is_node(n):
        return False

    return (str(n['type']) == ('T_' + t))


def is_node(l):
    '''return True if the value looks like a Node (has 'type' field)'''

    try:
        x = l['type']
        return True
    except:
        return False

def is_type(value, type_name):
    t = gdb.lookup_type(type_name)
    return (str(value.type) == str(t))
    # This doesn't work for list types for some reason...
    # return (gdb.types.get_basic_type(value.type) == gdb.types.get_basic_type(t))

def cast(node, type_name):
    '''wrap the gdb cast to proper node type'''

    # lookup the type with name 'type_name' and cast the node to it
    t = gdb.lookup_type(type_name)
    return node.cast(t.pointer())

# TODO: If this is a compound node type, it should return the base type
def get_base_node_type(node):
    node = cast(node, "Node")
    if is_node(node):
        return format_type(node['type'])

    return None

def add_indent(val, indent, add_newline=False):
    retval = ''
    if add_newline == True:
        retval += '\n'

    retval += "\n".join([(("\t" * indent) + l) for l in val.split("\n")])
    return retval

def getchars(arg):
    if (str(arg) == '0x0'):
        return str(arg)

    retval = '"'

    i=0
    while arg[i] != ord("\0"):
        character = int(arg[i].cast(gdb.lookup_type("char")))
        if chr(character) in string.printable:
            retval += "%c" % chr(character)
        else:
            retval += "\\x%x" % character
        i += 1

    retval += '"'

    return retval

def get_node_fields(node):
    nodefields = ["Node *", "Expr *"]
    type_name = str(node['type']).replace("T_", "")

    t = gdb.lookup_type(type_name)
    fields = []
    for v in t.values():
        for field in nodefields:
            if is_type(v, field):
                fields.append(v.name)

    return fields

def get_list_fields(node):
    listfields = ["List *"]
    type_name = str(node['type']).replace("T_", "")

    t = gdb.lookup_type(type_name)
    fields = []
    for v in t.values():
        for field in listfields:
            if is_type(v, field):
                fields.append(v.name)
    return fields

# Visibility options
NOT_NULL = "not_null"
HIDE_INVALID = "hide_invalid"
NEVER_SHOW = "never_show"
ALWAYS_SHOW = "always_show"

# TODO: generate these overrides in a yaml config file
FORMATTER_OVERRIDES = {
    'CaseWhen': {
        'fields':{
            'location': {'visibility': "never_show"},
        },
    },
    'ColumnDef': {
        'fields': {
            'identity': {
                'visibility': "not_null",
                'formatter': 'format_generated_when',
            },
            'generated': {
                'visibility': "not_null",
                'formatter': 'format_generated_when',
            },
            'collOid': {'visibility': "not_null"},
            'location': {'visibility': "never_show"},
        }
    },
    'Constraint': {
        'fields': {
            'location': {'visibility': "never_show"},
            'conname': {'visibility': "not_null"},
            'cooked_expr': {'visibility': "not_null"},
            'generated_when': {
                'visibility': "not_null",
                'formatter': 'format_generated_when',
            },
            'indexname': {'visibility': "not_null"},
            'indexspace': {'visibility': "not_null"},
            'access_method': {'visibility': "not_null"},
            'fk_matchtype': {
                'visibility': "not_null",
                'formatter': 'format_foreign_key_matchtype',
            },
            'fk_upd_action': {
                'visibility': "not_null",
                'formatter': 'format_foreign_key_actions',
            },
            'fk_del_action': {
                'visibility': "not_null",
                'formatter': 'format_foreign_key_actions',
            },
            'old_pktable_oid': {'visibility': "not_null"},
        },
        'datatype_methods': {
         }
    },
    'CreateStmt': {
        'fields': {
            'inhRelations': {'formatter': "format_optional_oid_list"},
        }
    },
    'DistinctExpr': {
        'fields':{
            'args': {'skip_tag': True},
            'opcollid': {'visibility': "not_null"},
            'inputcollid': {'visibility': "not_null"},
        },
    },
    'NullIfExpr': {
        'fields':{
            'args': {'skip_tag': True},
            'opcollid': {'visibility': "not_null"},
            'inputcollid': {'visibility': "not_null"},
        },
    },
    'OpExpr': {
        'fields':{
            'args': {'skip_tag': True},
            'opcollid': {'visibility': "not_null"},
            'inputcollid': {'visibility': "not_null"},
        },
    },
    'RangeTblEntry': {
        'fields': {
            'relid': {'visibility': "not_null"},
            'relkind': {'visibility': "not_null"},
            'rellockmode': {'visibility': "not_null"},
            'tablesample': {'visibility': "not_null"},
            'subquery': {'visibility': "not_null"},
            'security_barrier': {'visibility': "not_null"},
            'tablefunc': {'visibility': "not_null"},
            'ctename': {'visibility': "not_null"},
            'tcelevelsup': {'visibility': "not_null"},
            'enrname': {'visibility': "not_null"},
            'enrtuples': {'visibility': "not_null"},
            'inh': {'visibility': "not_null"},
            'requiredPerms': {'visibility': "not_null"},
            'checkAsUser': {'visibility': "not_null"},
            'selectedCols': {'visibility': "not_null"},
            'insertedCols': {'visibility': "not_null"},
            'updatedCols': {'visibility': "not_null"},
            'extraUpdatedCols': {'visibility': "not_null"},
            'eref': {'visibility': "never_show"},
        }
    },
    'RangeVar': {
        'fields': {
            'catalogname': {'visibility': "not_null"},
            'schemaname': {'visibility': "not_null"},
        }
    },
    'TargetEntry': {
        'fields':{
            'expr': {'skip_tag': True},
            'resname': {'visibility': "not_null"},
            'ressortgroupref': {'visibility': "not_null"},
            'resorigtbl': {'visibility': "not_null"},
            'resorigcol': {'visibility': "not_null"},
            'resjunk': {'visibility': "not_null"},
        },
    },
    'Var': {
        'fields':{
            'varno': {'formatter': "format_varno_field"},
            'vartypmod': {'visibility': "hide_invalid"},
            'varcollid': {'visibility': "not_null"},
            'varlevelsup': {'visibility': "not_null"},
            'location': {'visibility': "never_show"},
        },
    },
}

DEFAULT_DISPLAY_METHODS = {
    'regular_fields': 'format_regular_field',
    'node_fields': 'format_optional_node_field',
    'list_fields': 'format_optional_node_list',
    'datatype_methods': {
            'char *': 'format_string_pointer_field',
            'Bitmapset *': 'format_bitmapset_field',
    },
    'show_hidden': False,
}

def format_regular_field(node, field):
    return node[field]

def format_string_pointer_field(node, field):
    return getchars(node[field])

def format_char_field(node, field):
    char = format_char(node[field])
    return char

def format_bitmapset_field(node, field):
    return format_bitmapset(node[field])

def format_generated_when(node, field):
    generated_when = {
        'a': 'ATTRIBUTE_IDENTITY_ALWAYS',
        'd': 'ATTRIBUTE_IDENTITY_BY_DEFAULT',
        's': 'ATTRIBUTE_GENERATED_STORED',
    }

    fk_char = format_char(node[field])

    if generated_when.get(fk_char) != None:
        return generated_when.get(fk_char)

    return fk_char

def format_foreign_key_matchtype(node, field):
    foreign_key_matchtypes = {
        'f': 'FKCONSTR_MATCH_FULL',
        'p': 'FKCONSTR_MATCH_PARTIAL',
        's': 'FKCONSTR_MATCH_SIMPLE',
    }

    fk_char = format_char(node[field])

    if foreign_key_matchtypes.get(fk_char) != None:
        return foreign_key_matchtypes.get(fk_char)

    return fk_char


def format_foreign_key_actions(node, field):
    foreign_key_actions = {
        'a': 'FKONSTR_ACTION_NOACTION',
        'r': 'FKCONSTR_ACTION_RESTRICT',
        'c': 'FKCONSTR_ACTION_CASCADE',
        'n': 'FKONSTR_ACTION_SETNULL',
        'd': 'FKONSTR_ACTION_SETDEFAULT',
    }

    fk_char = format_char(node[field])

    if foreign_key_actions.get(fk_char) != None:
        return foreign_key_actions.get(fk_char)

    return fk_char

def format_varno_field(node, field):
    varno_type = {
        65000: "INNER_VAR",
        65001: "OUTER_VAR",
        65002: "INDEX_VAR",
    }

    varno = int(node[field])
    if varno_type.get(varno) != None:
        return varno_type.get(varno)

    return node[field]

def format_optional_node_field(node, fieldname, cast_to=None, skip_tag=False, print_null=False, indent=1):
    if cast_to != None:
        node = cast(node, cast_to)

    if str(node[fieldname]) != '0x0':
        if skip_tag == True:
            return add_indent('%s' % format_node(node[fieldname]), indent, True)
        else:
            return add_indent('[%s] %s' % (fieldname, format_node(node[fieldname])), indent, True)
    elif print_null == True:
        return add_indent("[%s] (NULL)" % fieldname, indent, True)

    return ''

def format_optional_node_list(node, fieldname, cast_to=None, skip_tag=False, newLine=True, print_null=False, indent=1):
    if cast_to != None:
        node = cast(node, cast_to)

    retval = ''
    indent_add = 0
    if str(node[fieldname]) != '0x0':
        if is_a(node[fieldname], 'OidList') or is_a(node[fieldname], 'IntList'):
            return format_optional_oid_list(node, fieldname, skip_tag, newLine, print_null, indent)

        if skip_tag == False:
            retval += add_indent('[%s]' % fieldname, indent, True)
            indent_add = 1

        if newLine == True:
            retval += '\n'
            retval += '%s' % format_node_list(node[fieldname], indent + indent_add, newLine)
        else:
            retval += ' %s' % format_node_list(node[fieldname], 0, newLine)
    elif print_null == True:
        return add_indent("[%s] (NIL)" % fieldname, indent, True)

    return retval

def format_optional_oid_list(node, fieldname, skip_tag=False, newLine=False, print_null=False, indent=1):
    retval = ''
    if str(node[fieldname]) != '0x0':
        node_type = format_type(node[fieldname]['type'])
        if skip_tag == False:
            retval += '[%s] %s' % (fieldname, format_node(node[fieldname]))
        else:
            retval += format_node(node[fieldname])

        retval = add_indent(retval, indent, True)
    elif print_null == True:
        retval += add_indent("[%s] (NIL)" % fieldname, indent, True)

    return retval

def debug_format_regular_field(node, field):
    print("debug_format_regular_field: %s[%s]: %s" % (get_base_node_type(node), field, node[field]))
    return node[field]

def debug_format_string_pointer_field(node, field):
    print("debug_format_string_pointer_field : %s[%s]: %s" % (get_base_node_type(node), field, format_string_pointer_field(node,field)))
    return format_string_pointer(node, field)

def debug_format_char_field(node, field):
    print("debug_format_char_field: %s[%s]: %s" % (get_base_node_type(node), field, format_char_field(node,field)))
    return format_char_field(node, field)

def debug_format_bitmapset_field(node, field):
    print("debug_format_bitmapset_field: %s[%s]: %s" % (get_base_node_type(node), field, format_bitmapset_field(node,field)))
    return format_bitmapset_field(node, field)

def debug_format_varno_field(node, field):
    print("debug_format_varno_field: %s[%s]: %s" % (get_base_node_type(node), field, format_varno_field(node,field)))
    return format_varno_field(node, field)

def debug_format_optional_node_list(node, fieldname, cast_to=None, skip_tag=False, newLine=True, print_null=False, indent=1):
    print("debug_format_optional_node_list: %s[%s]: %s" % (get_base_node_type(node), fieldname,
        format_optional_node_list(node, fieldname, cast_to, skip_tag, newLine, print_null, indent)))
    return format_optional_node_list(node, fieldname, cast_to, skip_tag, newLine, print_null, indent)

def debug_format_optional_oid_list(node, fieldname, skip_tag=False, newLine=False, print_null=False, indent=1):
    print("debug_format_optional_oid_list: %s[%s]: %s" % (get_base_node_type(node), fieldname,
        format_optional_oid_list(node, fieldname, skip_tag, newLine, print_null, indent)))
    return format_optional_oid_list(node, fieldname, newLine, skip_tag, print_null, indent)


class NodeFormatter(object):
    # Basic node information
    __node = None
    __node_type = None
    __type_str = None

    # String representations of individual fields in node
    __all_fields = None
    __regular_fields = None
    __node_fields = None
    __list_fields = None

    # Some node types are sub-types of other fields, for example a JoinState inherits a PlanState
    __nested_nodes = None

    # Handle extra fields differently than other types
    # TODO: - remove extra fields from __regular_feilds
    #       - set a special method to format these fields in a config file
    __default_regular_display_method = None
    __formatter_overrides = None

    # String representation of the types to match to generate the above lists
    __list_types = None
    __node_types = None
    def __init__(self, node, typecast=None):
        # TODO: get node and list types from yaml config OR check each field
        #       for a node 'signature'
        # TODO: this should be done in a class method
        self.__list_types = ["List *"]
        self.__node_types = ["Node *", "Expr *", "FromExpr *", "OnConflictExpr *", "RangeVar *", "TypeName *", "ExprContext *", "MemoryContext *", "CollateClause *", "struct SelectStmt *", "Alias *", "struct Plan *"]
        self.__inherited_node_types = ['PlanState', 'JoinState']

        # TODO: Make the node lookup able to handle inherited types(like Plan nodes)
        if typecast == None:
            typecast = str(node['type'])
        self.__type_str = typecast
        self.__node = cast(node, self.type)

        # Get methods for display
        self.__default_display_methods = DEFAULT_DISPLAY_METHODS
        self.__default_regular_visibility = ALWAYS_SHOW
        self.__default_list_visibility = NOT_NULL
        self.__default_node_visibility = NOT_NULL
        self.__default_skip_tag = False
        self.__formatter_overrides = FORMATTER_OVERRIDES.get(self.type)
        #print("NodeFormatter:", self.type)

    def get_datatype_override(self, field):
        if self.__formatter_overrides != None:
            datatype_overrides = self.__formatter_overrides.get('datatype_methods')
            if datatype_overrides != None:
                return datatype_overrides.get(str(self.field_datatype(field)))
        return None

    def get_field_override(self, field, override_type):
        if self.__formatter_overrides != None:
            field_overrides = self.__formatter_overrides.get('fields')
            if field_overrides != None:
                field_override = field_overrides.get(field)
                if field_override != None:
                    return field_override.get(override_type)
        return None

    def get_display_method(self, field):
        # Individual field overrides are a higher priority than type
        # overrides so print them first
        field_override_method_name = self.get_field_override(field, 'formatter')
        if field_override_method_name != None:
            return globals()[field_override_method_name]

        # Datatype methods are only for regular fields
        datatype_override_method = self.get_datatype_override(field)
        if datatype_override_method != None:
            return globals()[datatype_override_method]

        # Check if this datatype has a generic dumping method
        default_type_method = self.__default_display_methods['datatype_methods'].get(str(self.field_datatype(field)))
        if default_type_method != None:
            return globals()[default_type_method]

        if field in self.__regular_fields:
            return globals()[self.__default_display_methods['regular_fields']]
        elif field in self.__node_fields:
            return globals()[self.__default_display_methods['node_fields']]
        elif field in self.__list_fields:
            return globals()[self.__default_display_methods['list_fields']]

        raise Exception("Did not find a display method for %s[%s]" % (self.type, field))


    def get_display_mode(self, field):
        # If the global 'show_hidden' is set, then this command shal always
        # return ALWAYS_SHOW
        if self.__default_display_methods['show_hidden'] == True:
            return ALWAYS_SHOW

        override_string = self.get_field_override(field, 'visibility')
        if override_string != None:
            return override_string

        if field in self.__regular_fields:
            return self.__default_regular_visibility
        if field in self.__list_fields:
            return self.__default_list_visibility
        if field in self.__node_fields:
            return self.__default_node_visibility

        return ALWAYS_SHOW

    def is_skip_tag(self, field):
        # If the global 'show_hidden' is set, always show tag
        if self.__default_display_methods['show_hidden'] == True:
            return False

        skip_tag = self.get_field_override(field, 'skip_tag')
        if skip_tag != None:
            return skip_tag

        return self.__default_skip_tag

    @property
    def type(self):
        if self.__node_type == None:
            self.__node_type = format_type(self.__type_str)
        return self.__node_type

    @property
    def fields(self):
        if self.__all_fields == None:
            self.__all_fields = []
            t = gdb.lookup_type(self.type)

            for index in range(0, len(t.values())):
                field = t.values()[index]
                if index == 0:
                    # The node['type'] field is just a tag that we already know
                    skip = False
                    if field.name == "type":
                        skip = True
                    # The node['xpr'] field is just a wrapper around node['type']
                    elif field.name == "xpr" and self.is_type(field, "Expr"):
                        skip = True
                    # If the first field is an inherited type, we dump the
                    # sub fields recursively in self.format()
                    else:
                        for tag in self.__inherited_node_types:
                            if self.is_type(field, tag):
                                skip = True

                                nested_node = NodeFormatter(self.__node, str(field.type))
                                if self.__nested_nodes == None:
                                    self.__nested_nodes = []
                                self.__nested_nodes.append((field.name, nested_node))
                                break

                    if skip:
                        continue

                self.__all_fields.append(field.name)

        return self.__all_fields

    @property
    def list_fields(self):
        if self.__list_fields == None:
            self.__list_fields = []

            t = gdb.lookup_type(self.type)
            for v in t.values():
                for field in self.__list_types:
                    if self.is_type(v, field):
                        self.__list_fields.append(v.name)

        return self.__list_fields

    @property
    def node_fields(self):
        if self.__node_fields == None:
            self.__node_fields = []

            t = gdb.lookup_type(self.type)
            for v in t.values():
                for field in self.__node_types:
                    if self.is_type(v, field):
                        self.__node_fields.append(v.name)

        return self.__node_fields

    @property
    def regular_fields(self):
        if self.__regular_fields == None:
            self.__regular_fields = []

            self.__regular_fields = [field for field in self.fields if field not in self.list_fields + self.node_fields]

        return self.__regular_fields

    # TODO: should this be a class method?
    def is_type(self, value, type_name):
        t = gdb.lookup_type(type_name)
        return (str(value.type) == str(t))
        # This doesn't work for list types for some reason...
        # return (gdb.types.get_basic_type(value.type) == gdb.types.get_basic_type(t))

    def field_datatype(self, field):
        return gdb.types.get_basic_type(self.__node[field].type)

    def format(self):
        retval = self.format_regular_fields()

        # If this is a nested node type, dump sub types
        retval += self.format_nested_fields()

        for field in self.fields:
            if field in self.__regular_fields:
                continue

            display_mode = self.get_display_mode(field)
            print_null = False
            if display_mode == NEVER_SHOW:
                continue
            elif display_mode == ALWAYS_SHOW:
                print_null = True

            skip_tag = self.is_skip_tag(field)

            display_method = self.get_display_method(field)
            retval += display_method(self.__node, field, skip_tag=skip_tag, print_null=print_null)

        return retval

    def format_regular_fields(self):
        # TODO: get this value from config file
        max_regular_field_chars = 140
        retval = self.type
        retval += " ["

        newline_padding_chars = len(retval)

        fieldcount = 0
        retline = ""
        for field in self.regular_fields:
            fieldcount +=1
            display_mode = self.get_display_mode(field)
            if display_mode == NEVER_SHOW:
                continue

            # Some fields don't have a meaning if they aren't given a value
            if display_mode == NOT_NULL:
                field_datatype = self.field_datatype(field)
                empty_value = gdb.Value(0).cast(field_datatype)
                if self.__node[field] == empty_value:
                    continue

            # Some fields are initialized to -1 if they are not used
            if display_mode == HIDE_INVALID:
                field_datatype = self.field_datatype(field)
                empty_value = gdb.Value(-1).cast(field_datatype)
                if self.__node[field] == empty_value:
                    continue

            display_method = self.get_display_method(field)
            value = display_method(self.__node, field)


            # TODO: display method did not return a value- fallback to the
            # default display method
            #if value == None:
            #    continue

            if fieldcount > 1:
                # TODO: track current indentation level
                if len(retline) > max_regular_field_chars:
                    retval += retline + '\n' + (' ' * newline_padding_chars)
                    retline = ''
                elif len(retline) > 0:
                    retline += ' '

            retline += "%(field)s=%(value)s" % {
                'field': field,
                'value': value
            }

        retval += retline
        retval += ']'

        return retval

    def format_nested_fields(self):
        retval = ''
        if self.__nested_nodes != None:
            for fieldname, node in self.__nested_nodes:
                retval += add_indent('[%s]' % fieldname, 1, True)
                retval += add_indent(node.format(), 2, True)
        return retval

class PgPrintCommand(gdb.Command):
    "print PostgreSQL structures"

    def __init__(self):
        super(PgPrintCommand, self).__init__("pgprint", gdb.COMMAND_SUPPORT,
                                             gdb.COMPLETE_NONE, False)

    def invoke(self, arg, from_tty):

        arg_list = gdb.string_to_argv(arg)
        if len(arg_list) != 1:
            print("usage: pgprint var")
            return

        l = gdb.parse_and_eval(arg_list[0])

        if not is_node(l):
            print("not a node type")

        print(format_node(l))


PgPrintCommand()
