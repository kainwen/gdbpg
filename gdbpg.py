import gdb

PlanNodes = ['Result', 'Repeat', 'Append', 'Sequence', 'Motion', 'AOCSScan',
        'BitmapAnd', 'BitmapOr', 'Scan', 'SeqScan', 'TableScan',
        'IndexScan', 'DynamicIndexScan', 'BitmapIndexScan',
        'BitmapHeapScan', 'BitmapAppendOnlyScan', 'BitmapTableScan',
        'DynamicTableScan', 'TidScan', 'SubqueryScan', 'FunctionScan',
        'TableFunctionScan', 'ValuesScan', 'ExternalScan', 'AppendOnlyScan',
        'Join', 'NestLoop', 'MergeJoin', 'HashJoin', 'ShareInputScan',
        'Material', 'Sort', 'Agg', 'Window', 'Unique', 'Hash', 'SetOp',
                'Limit', 'DML', 'SplitUpdate', 'AssertOp', 'RowTrigger',
                'PartitionSelector' ]

def format_plan_tree(tree, indent=0):
    'formats a plan (sub)tree, with custom indentation'

    # if the pointer is NULL, just return (null) string
    if (str(tree) == '0x0'):
        return '-> (NULL)'

    retval = '''
-> %(type)s (cost=%(startup).3f...%(total).3f rows=%(rows)s width=%(width)s) id=%(plan_node_id)s
\ttarget list:
%(target)s''' % {
        'type': format_type(tree['type']),    # type of the Node
        'startup': float(tree['startup_cost']),    # startup cost
        'total': float(tree['total_cost']),    # total cost
        'rows': str(tree['plan_rows']),    # number of rows
        'width': str(tree['plan_width']),    # tuple width (no header)
        'plan_node_id': str(tree['plan_node_id']),

        # format target list
        'target': format_node_list(tree['targetlist'], 2, True)
        }

    if (str(tree['initPlan']) != '0x0'):
        retval +='''
\tinitPlan:
%(initPlan)s''' % {
            'initPlan': format_node_list(tree['initPlan'], 2, True)
        }

    if (str(tree['qual']) != '0x0'):
        retval +='''
\tqual:
%(qual)s''' % {
            'qual': format_node_list(tree['qual'], 2, True)
        }

    if is_a(tree, 'Result'):
        result = cast(tree, 'Result')
        if str(result['resconstantqual']) != '0x0':
            # Resconstant qual might be a list
            if is_a(result['resconstantqual'], 'List'):
                resconstantqual = cast(result['resconstantqual'], 'List')
            else:
                resconstantqual = result['resconstantqual']

            retval+='''
\tresconstantqual:
%(resconstantqual)s''' % {
                'resconstantqual': format_node(resconstantqual, 2)
            }


    if is_a(tree, 'HashJoin') or is_a(tree, 'Join') or is_a(tree, 'NestLoop') or is_a(tree, 'MergeJoin'):
        join = cast(tree, 'Join')
        if str(join['joinqual']) != '0x0':
            retval+='''
\tjoinqual:
%(joinqual)s''' % {
                'joinqual': format_node_list(join['joinqual'], 2, True)
            }

    if is_a(tree, 'Append'):
        append = cast(tree, 'Append')
        retval += '''
\t%(appendplans)s''' % {
        # format Append subplans
        'appendplans': format_appendplan_list(append['appendplans'], 0)
        }
    elif is_a(tree, 'SubqueryScan'):
        subquery = cast(tree, 'SubqueryScan')
        retval += '''
\t%(subplan)s''' % {
        'subplan': format_plan_tree(subquery['subplan'], 0)
        }
    else:
    # format all the important fields (similarly to EXPLAIN)
        retval +='''
\t%(left)s
\t%(right)s''' % {

        # left subtree
        'left': format_plan_tree(tree['lefttree'], 0),

        # right subtree
        'right': format_plan_tree(tree['righttree'], 0)
        }

    return add_indent(retval, indent + 1)

def format_query_info(node, indent=0):
    'formats a query node with custom indentation'
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = '''          type: %(type)s
  command type: %(commandType)s
  query source: %(querySource)s
   can set tag: %(canSetTag)s
   range table:
%(rtable)s
      jointree:
%(jointree)s
    targetList:
%(targetList)s
 returningList:
%(returningList)s
''' % {
        'type': format_type(node['type']),
        'commandType': format_type(node['commandType']),
        'querySource': format_type(node['querySource']),
        'canSetTag': (int(node['canSetTag']) == 1),
        'rtable': format_node_list(node['rtable'], 1, True),
        'jointree': format_node(node['jointree']),
        'targetList': format_node(node['targetList']),
        'returningList': format_node(node['returningList']),
      }

    return retval

def format_appendplan_list(lst, indent):
    retval = format_node_list(lst, indent, True)
    return add_indent(retval, indent + 1)

def format_alter_table_cmd(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    if (str(node['name']) == '0x0'):
        name = '(NIL)'
    else:
        name = node['name']

    retval = '''AlterTableCmd (subtype=%(subtype)s name=%(name)s behavior=%(behavior)s part_expanded=%(part_expanded)s)''' % {
        'subtype': node['subtype'],
        'name': name,
        'behavior': node['behavior'],
        'part_expanded': (int(node['part_expanded']) == 1)
    }

    if (str(node['def']) != '0x0'):
        retval += '\n'
        retval += add_indent('[definition] %s' % format_node(node['def']), 1)

    #if (str(node['transform']) != '0x0'):
    #    retval += '\n'
    #    retval += add_indent('- [transform] %s' % format_node(node['transform']), 1)

    #if (str(node['partoids']) != '0x0'):
    #    retval += '\n'
    #    retval += add_indent('- [partoids] %s' % format_oid_list(node['partoids']), 1)

    return add_indent(retval, indent)

def format_alter_partition_cmd(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'AlterPartitionCmd (location=%(location)s)' % {
        'location': node['location']
    }

    if (str(node['partid']) != '0x0'):
        retval += '\n'
        retval += add_indent('[partid] %s' % format_node(node['partid']), 1)

    if (str(node['arg1']) != '0x0'):
        retval += '\n'
        retval += add_indent('[arg1] %s' % format_node(node['arg1']), 1)

    if (str(node['arg2']) != '0x0'):
        retval += '\n'
        retval += add_indent('[arg2] %s' % format_node(node['arg2']), 1)

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

    if (str(node['pNode']) != '0x0'):
        retval += '\n'
        retval += add_indent('[pNode] %s' % format_node(node['pNode']), 1)

    if (str(node['topRule']) != '0x0'):
        retval += '\n'
        retval += add_indent('[topRule] %s' % format_node(node['topRule']), 1)

    return add_indent(retval, indent)

def format_partition_node(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionNode'


    if (str(node['part']) != '0x0'):
        retval += '\n'
        retval += add_indent('[part] %s' % format_node(node['part']), 1)

    if (str(node['default_part']) != '0x0'):
        retval += '\n'
        retval += add_indent('[default_part] %s' % format_node(node['default_part']), 1)

    if (str(node['rules']) != '0x0'):
        retval += '\n'
        retval += add_indent('[rules] %s' % format_node_list(node['rules'], 0, True), 1)

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

    if (str(node['boundSpec']) != '0x0'):
        retval += '\n'
        retval += add_indent('[boundSpec] %s' % format_node(node['boundSpec']), 1)

    if (str(node['subSpec']) != '0x0'):
        retval += '\n'
        retval += add_indent('[subSpec] %s' % format_node(node['subSpec']), 1)

    if (str(node['storeAttr']) != '0x0'):
        retval += '\n'
        retval += add_indent('[storeAttr] %s' % format_node(node['storeAttr']), 1)

    if (str(node['colencs']) != '0x0'):
        retval += '\n'
        retval += add_indent('[colencs] %s' % format_node_list(node['colencs'], 0, True), 1)


    return add_indent(retval, indent)

def format_partition_bound_spec(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionBoundSpec (pWithTnameStr=%(pWithTnameStr)s location=%(location)s)' % {
        'pWithTnameStr': node['pWithTnameStr'],
        'location': node['location'],
    }
    if (str(node['partStart']) != '0x0'):
        retval += '\n'
        retval += add_indent('[partStart] %s' % format_node(node['partStart']), 1)

    if (str(node['partEnd']) != '0x0'):
        retval += '\n'
        retval += add_indent('[partEnd] %s' % format_node(node['partEnd']), 1)

    if (str(node['partEvery']) != '0x0'):
        retval += '\n'
        retval += add_indent('[partEvery] %s' % format_node(node['partEvery']), 1)

    if (str(node['everyGenList']) != '0x0'):
        retval += '\n'
        retval += add_indent('[everyGenList] %s' % format_node_list(node['everyGenList'], 0, True), 1)


    return add_indent(retval, indent)

def format_partition_range_item(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'PartitionRangeItem (partedge=%(partedge)s everycount=%(everycount)s location=%(location)s)' % {
        'partedge': node['partedge'],
        'everycount': node['everycount'],
        'location': node['location'],
    }

    if (str(node['partRangeVal']) != '0x0'):
        retval += '\n'
        retval += add_indent('[partRangeVal] %s' % format_node_list(node['partRangeVal'], 0, True), 1)


    return add_indent(retval, indent)

def format_partition(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'Partition (partid=%(partid)s parrelid=%(parrelid)s parkind=%(parkind)s parlevel=%(parlevel)s paristemplate=%(paristemplate)s parnatts=%(parnatts)s paratts=%(paratts)s parclass=%(parclass)s)' % {
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

def format_type_cast(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'TypeCast (location=%(location)s)' % {
        'location': node['location'],
    }


    if (str(node['typeName']) != '0x0'):
        retval += '\n'
        retval += add_indent('[typeName] %s' % format_node(node['typeName']), 1)

    if (str(node['arg']) != '0x0'):
        retval += '\n'
        retval += add_indent('[arg] %s' % format_node(node['arg']), 1)

    return add_indent(retval, indent)


def format_def_elem(node, indent=0):
    if (str(node) == '0x0'):
        return '(NIL)'

    retval = 'DefElem (defname=%(defname)s defaction=%(defaction)s)' % {
        'defname': node['defname'],
        'defaction': node['defaction'],
    }

    if (str(node['arg']) != '0x0'):
        retval += '\n'
        retval += add_indent('[arg] %s' % format_node(node['arg']), 1)

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



def format_type(t, indent=0):
    'strip the leading T_ from the node type tag'

    t = str(t)

    if t.startswith('T_'):
        t = t[2:]

    return add_indent(t, indent)


def format_int_list(lst, indent=0):
    'format list containing integer values directly (not warapped in Node)'

    # handle NULL pointer (for List we return NIL
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    item = lst['head']

    # walk the list until we reach the last item
    while str(item) != '0x0':

        # get item from the list and just grab 'int_value as int'
        tlist.append(int(item['data']['int_value']))

        # next item
        item = item['next']

    return add_indent(str(tlist), indent)


def format_oid_list(lst, indent=0):
    'format list containing Oid values directly (not warapped in Node)'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    item = lst['head']

    # walk the list until we reach the last item
    while str(item) != '0x0':

        # get item from the list and just grab 'oid_value as int'
        tlist.append(int(item['data']['oid_value']))

        # next item
        item = item['next']

    return add_indent(str(tlist), indent)


def format_node_list(lst, indent=0, newline=False):
    'format list containing Node values'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
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

    retval = str(tlist)
    if newline:
        retval = "\n".join([str(t) for t in tlist])

    return add_indent(retval, indent)


def format_char(value):
    '''convert the 'value' into a single-character string (ugly, maybe there's a better way'''

    str_val = str(value.cast(gdb.lookup_type('char')))

    # remove the quotes (start/end)
    return str_val.split(' ')[1][1:-1]


def format_relids(relids):
    return '(not implemented)'


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

    if is_a(node, 'TargetEntry'):

        # we assume the list contains Node instances (probably safe for Plan fields)
        node = cast(node, 'TargetEntry')

        name_ptr = node['resname'].cast(gdb.lookup_type('char').pointer())
        name = "(NULL)"
        if str(name_ptr) != '0x0':
            name = '"' + (name_ptr.string()) + '"'

        retval = 'TargetEntry (resno=%(resno)s resname=%(name)s origtbl=%(tbl)s origcol=%(col)s junk=%(junk)s expr=[%(expr)s])' % {
            'resno': node['resno'],
            'name': name,
            'tbl': node['resorigtbl'],
            'col': node['resorigcol'],
            'junk': (int(node['resjunk']) == 1),
            'expr': format_node(node['expr'])
        }

    elif is_a(node, 'Var'):

        # we assume the list contains Node instances (probably safe for Plan fields)
        node = cast(node, 'Var')

        if node['varno'] == 65000:
            varno = "INNER"
        elif node['varno'] == 65001:
            varno = "OUTER"
        else:
            varno = node['varno']

        retval = 'Var (varno=%(no)s varattno=%(attno)s levelsup=%(levelsup)s)' % {
            'no': varno,
            'attno': node['varattno'],
            'levelsup': node['varlevelsup']
        }

    elif is_a(node, 'Const'):
        node = cast(node, 'Const')

        retval = format_const(node)

    elif is_a(node, 'Aggref'):
        node = cast(node, 'Aggref')

        retval = '''Aggref (aggfnoid=%(fnoid)s aggtype=%(aggtype)s aggstage=%(stage)s)
\tAggref Args:
%(args)s''' % {
            'fnoid': node['aggfnoid'],
            'aggtype': node['aggtype'],
            'stage': node['aggstage'],
            'args': format_node_list(node['args'], 2, True)
        }

    elif is_a(node, 'CaseExpr'):
        node = cast(node, 'CaseExpr')

        retval = '''CaseExpr (casetype=%(casetype)s defresult=%(defresult)s arg=%(arg)s)
\tCaseExpr Args:
%(args)s''' % {
            'casetype': node['casetype'],
            'defresult': format_node(node['defresult']),
            'arg': format_node(node['arg']),
            'args': format_node_list(node['args'], 2, True)
        }

    elif is_a(node, 'CoalesceExpr'):
        node = cast(node, 'CoalesceExpr')

        retval = format_coalesce_expr(node)

    elif is_a(node, 'CaseWhen'):
        node = cast(node, 'CaseWhen')

        retval = '''CaseWhen (expr=%(expr)s result=%(result)s)''' % {
                'expr': format_node(node['expr']),
                'result': format_node(node['result'])
        }


    elif is_a(node, 'RangeTblRef'):

        node = cast(node, 'RangeTblRef')

        retval = 'RangeTblRef (rtindex=%d)' % (int(node['rtindex']), )

    elif is_a(node, 'RelOptInfo'):

        node = cast(node, 'RelOptInfo')

        retval = 'RelOptInfo (kind=%(kind)s relids=%(relids)s rtekind=%(rtekind)s relid=%(relid)s rows=%(rows)s width=%(width)s fk=%(fk)s)' % {
            'kind': node['reloptkind'],
            'rows': node['rows'],
            'width': node['width'],
            'relid': node['relid'],
            'relids': format_relids(node['relids']),
            'rtekind': node['rtekind'],
            'fk': (int(node['has_fk_join']) == 1)
        }

    elif is_a(node, 'RangeTblEntry'):

        node = cast(node, 'RangeTblEntry')

        retval = 'RangeTblEntry (kind=%(rtekind)s relid=%(relid)s)' % {
            'relid': node['relid'],
            'rtekind': node['rtekind']
    #'relkind' : format_char(node['relkind'])
        }

    elif is_a(node, 'GenericExprState'):

        node = cast(node, 'GenericExprState')
        retval = format_generic_expr_state(node)

    elif is_a(node, 'PlannerInfo'):

        retval = format_planner_info(node)

    elif is_a(node, 'PlannedStmt'):

        node = cast(node, 'PlannedStmt')

        retval = format_planned_stmt(node)

    elif is_a(node, 'List'):

        node = cast(node, 'List')

        retval = format_node_list(node, 0, True)

    elif is_a(node, 'Plan'):

        retval = format_plan_tree(node)

    elif is_a(node, 'RestrictInfo'):

        node = cast(node, 'RestrictInfo')

        retval = '''RestrictInfo (pushed_down=%(push_down)s can_join=%(can_join)s delayed=%(delayed)s)
%(clause)s
%(orclause)s''' % {
            'clause': format_node(node['clause'], 1),
            'orclause': format_node(node['orclause'], 1),
            'push_down': (int(node['is_pushed_down']) == 1),
            'can_join': (int(node['can_join']) == 1),
            'delayed': (int(node['outerjoin_delayed']) == 1)
        }

    elif is_a(node, 'OpExpr'):

        node = cast(node, 'OpExpr')

        retval = format_op_expr(node)

    elif is_a(node, 'DistinctExpr'):

        node = cast(node, 'OpExpr')

        retval = format_op_expr(node)

    elif is_a(node, 'FuncExpr'):

        node = cast(node, 'FuncExpr')

        retval = format_func_expr(node)

    elif is_a(node, 'ScalarArrayOpExpr'):

        node = cast(node, 'ScalarArrayOpExpr')

        retval = format_scalar_array_op_expr(node)

    elif is_a(node, 'BoolExpr'):

        node = cast(node, 'BoolExpr')

        #print(node)

        retval = format_bool_expr(node)

    elif is_a(node, 'FromExpr'):

        node = cast(node, 'FromExpr')

        retval = format_from_expr(node)


    elif is_a(node, 'AlterTableCmd'):

        node = cast(node, 'AlterTableCmd')

        retval = format_alter_table_cmd(node)

    elif is_a(node, 'AlterPartitionCmd'):

        node = cast(node, 'AlterPartitionCmd')

        retval = format_alter_partition_cmd(node)

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

    elif is_a(node, 'PartitionBoundSpec'):

        node = cast(node, 'PartitionBoundSpec')

        retval = format_partition_bound_spec(node)

    elif is_a(node, 'PartitionRangeItem'):

        node = cast(node, 'PartitionRangeItem')

        retval = format_partition_range_item(node)

    elif is_a(node, 'Partition'):

        node = cast(node, 'Partition')

        retval = format_partition(node)

    elif is_a(node, 'DefElem'):

        node = cast(node, 'DefElem')

        retval = format_def_elem(node)

    elif is_a(node, 'Param'):

        node = cast(node, 'Param')

        retval = format_param(node)

    elif is_a(node, 'String'):

        retval = 'String: %s' % node

    elif is_a(node, 'SubPlan'):

        node = cast(node, 'SubPlan')

        retval = '''SubPlan (subLinkType=%(subLinkType)s plan_id=%(plan_id)s plan_name=%(plan_name)s)
%(args)s''' % {
            'subLinkType': node['subLinkType'],
            'plan_id': node['plan_id'],
            'plan_name': node['plan_name'],
            'args': format_node_list(node['args'], 1, True)
        }

    elif is_a(node, 'PartitionRule'):

        node = cast(node, 'PartitionRule')

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

        if (str(node['parrangeevery']) != '0x0'):
            retval += '\n\t[parrangeevery] %(parrangeevery)s' % {
                'parrangeevery': format_node_list(cast(node['parrangeevery'], 'List'), 0, True),
            }

        if (str(node['parlistvalues']) != '0x0'):
            retval += '\n\t[parlistvalues] %(parlistvalues)s' % {
                'parlistvalues': format_node_list(node['parlistvalues']),
            }

        if (str(node['parreloptions']) != '0x0'):
            retval += '\n\t[parreloptions] %(parreloptions)s' % {
            'parlistvalues': format_node_list(node['parlistvalues']),
        }

        if (str(node['children']) != '0x0'):
            retval += '\n'
            retval += add_indent('[children] %s' % format_node(node['children']),1)

    elif is_a(node, 'TypeCast'):

        node = cast(node, 'TypeCast')

        retval = format_type_cast(node)

    elif is_a(node, 'OidList'):

        retval = 'OidList: %s' % format_oid_list(node)


    elif is_a(node, 'Query'):

        retval = format_query_info(node)


    elif is_plannode(node):
        node = cast(node, 'Plan')
        retval = format_plan_tree(node)


    else:
        # default - just print the type name
        retval = format_type(type_str)

    return add_indent(str(retval), indent)

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


def format_planned_stmt(plan, indent=0):

    retval = '''          type: %(type)s
       planGen: %(planGen)s
   can set tag: %(can_set_tag)s
     transient: %(transient)s
               
     plan tree: %(tree)s
   range table:
%(rtable)s
 relation OIDs: %(relation_oids)s
   result rels: %(result_rels)s
  utility stmt: %(util_stmt)s
      subplans: %(subplans)s''' % {
        'type': plan['commandType'],
        'planGen': plan['planGen'],
    #'qid' : plan['queryId'],
    #'nparam' : plan['nParamExec'],
    #'has_returning' : (int(plan['hasReturning']) == 1),
    #'has_modify_cte' : (int(plan['hasModifyingCTE']) == 1),
        'can_set_tag': (int(plan['canSetTag']) == 1),
        'transient': (int(plan['transientPlan']) == 1),
    #'row_security' : (int(plan['hasRowSecurity']) == 1),
        'tree': format_plan_tree(plan['planTree']),
        'rtable': format_node_list(plan['rtable'], 1, True),
        'relation_oids': format_oid_list(plan['relationOids']),
        'result_rels': format_int_list(plan['resultRelations']),
        'util_stmt': format_node(plan['utilityStmt']),
        'subplans': format_node_list(plan['subplans'], 1, True)
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


def format_op_expr(node, indent=0):

    nodetag = 'OpExpr'

    if is_a(cast(node, 'Node'), 'DistinctExpr'):
        nodetag =  'DistinctExpr'

    retval = """%(nodetag)s [opno=%(opno)s opfuncid=%(opfuncid)s opresulttype=%(opresulttype)
%(clauses)s""" % {
        'nodetag': nodetag,
        'opno': node['opno'],
        'opfuncid': node['opfuncid'],
        'opresulttype': node['opresulttype'],
        'clauses': format_node_list(node['args'], 1, True)
    }

def format_func_expr(node, indent=0):

    retval = """FuncExpr [funcid=%(funcid)s funcresulttype=%(funcresulttype)s funcretset=%(funcretset)s funcformat=%(funcformat)s""" % {
        'funcid': node['funcid'],
        'funcresulttype': node['funcresulttype'],
        'funcretset': (int(node['funcretset']) == 1),
        'funcformat': node['funcformat'],
    }


    retval += ' location=%(location)s is_tablefunc=%(is_tablefunc)s]\n' % {
        'location': node['location'],
        'is_tablefunc': (int(node['is_tablefunc']) == 1),
    }

    retval += """%(args)s""" % {
        'args': format_node_list(node['args'], 1, True)
    }

    return add_indent(retval, indent)

def format_scalar_array_op_expr(node, indent=0):
    return """ScalarArrayOpExpr [opno=%(opno)s opfuncid=%(opfuncid)s useOr=%(useOr)s]
%(clauses)s""" % {
        'opno': node['opno'],
        'opfuncid': node['opfuncid'],
        'useOr': (int(node['useOr']) == 1),
        'clauses': format_node_list(node['args'], 1, True)
    }


def format_coalesce_expr(node, indent=0):
    retval = "CoalesceExpr [coalescetype=%(coalescetype)s location=%(location)s]" % {
        'coalescetype': node['coalescetype'],
        'location': node['location'],
        }

    if (str(node['args']) != '0x0'):
        retval += '\n'
        retval += add_indent('[args] %s' % format_node_list(node['args'], 0, True), 1)

    return add_indent(retval, indent)

def format_bool_expr(node, indent=0):

    return """BoolExpr [op=%(op)s]
%(clauses)s""" % {
        'op': node['boolop'],
        'clauses': format_node_list(node['args'], 1, True)
    }

def format_from_expr(node):
    retval = """FromExpr
%(fromlist)s""" % { 'fromlist': format_node_list(node['fromlist'], 1, True) }
    if (str(node['quals']) != '0x0'):
        retval +='''
quals:
%(quals)s''' % {
            'quals': format_node(node['quals'],1)
        }
    return retval

def format_const(node):
    retval = "Const (consttype=%s" % node['consttype']
    if (str(node['consttypmod']) != '0x0'):
        retval += " consttypmod=%s" % node['consttypmod']

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

    retval += ')'
    return retval

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


def cast(node, type_name):
    '''wrap the gdb cast to proper node type'''

    # lookup the type with name 'type_name' and cast the node to it
    t = gdb.lookup_type(type_name)
    return node.cast(t.pointer())


def add_indent(val, indent):

    return "\n".join([(("\t" * indent) + l) for l in val.split("\n")])


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
