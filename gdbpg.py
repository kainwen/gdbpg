import gdb
import string

# Visibility options
NOT_NULL = "not_null"
HIDE_INVALID = "hide_invalid"
NEVER_SHOW = "never_show"
ALWAYS_SHOW = "always_show"

# TODO: Put these fields in a config file
PlanNodes = ['Result', 'Repeat', 'ModifyTable','Append', 'Sequence', 'Motion', 
        'AOCSScan', 'BitmapAnd', 'BitmapOr', 'Scan', 'SeqScan', 'DynamicSeqScan',
        'TableScan', 'IndexScan', 'DynamicIndexScan', 'BitmapIndexScan',
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

# TODO: Put these defaults config file
DEFAULT_DISPLAY_METHODS = {
    'regular_fields': 'format_regular_field',
    'node_fields': 'format_optional_node_field',
    'list_fields': 'format_optional_node_list',
    'tree_fields': 'format_optional_node_field',
    'datatype_methods': {
            'char *': 'format_string_pointer_field',
            'const char *': 'format_string_pointer_field',
            'Bitmapset *': 'format_bitmapset_field',
            'struct gpmon_packet_t': 'format_gpmon_packet_field',
            'struct timeval': 'format_timeval_field',
    },
    'show_hidden': False,
    'max_recursion_depth': 30
}

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
    'Const': {
        'fields': {
            'consttypmod': {'visibility': "hide_invalid"},
            'constcollid': {'visibility': "not_null"},
            'location': {'visibility': "never_show"},
        },
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
            'trig1Oid': {'visibility': "not_null"},
            'trig2Oid': {'visibility': "not_null"},
            'trig3Oid': {'visibility': "not_null"},
            'trig4Oid': {'visibility': "not_null"},
        },
        'datatype_methods': {
         }
    },
    'CreateStmt': {
        'fields': {
            'inhRelations': {'formatter': "format_optional_oid_list"},
        }
    },
    'DefElem': {
        'fields': {
            'defnamespace': {'visibility': "not_null"},
        },
    },
    'DistinctExpr': {
        'fields': {
            'args': {'skip_tag': True},
            'opcollid': {'visibility': "not_null"},
            'inputcollid': {'visibility': "not_null"},
        },
    },
    'EquivalenceClass': {
        'fields': {
            # TODO: These fields are nice to dump recursively, but 
            # they potentially have backwards references to their parents.
            # Need a way to detect this condition and stop dumping
            'ec_sources': {'formatter': 'minimal_format_node_field', },
            'ec_derives': {'formatter': 'minimal_format_node_field', },
        },
    },
    'EState': {
        'fields':{
            'es_plannedstmt': {'visibility': "never_show"},
            # TODO: These fields crash gdbpg.py
            'es_sharenode': {'visibility': "never_show"},
        },
    },
    'ExprContext': {
        'fields':{
            'ecxt_estate': {'visibility': "never_show"},
        },
    },
    'IndexOptInfo': {
        'fields': {
            'rel': {'formatter': 'minimal_format_node_field', }
        },
    },
    'FuncExprState': {
        'fields':{
            # TODO: These fields crash gdbpg.py
            'fp_arg': {'visibility': "never_show"},
            'fp_datum': {'visibility': "never_show"},
            'fp_null': {'visibility': "never_show"},
        },
    },
    # TODO: It would be nice to be able to recurse into memory contexts and
    #       print the tree, but need to make its own NodeFormatter in order
    #       to make its output look like a tree
    'MemoryContextData': {
        'fields':{
            'methods': {'visibility': "never_show"},
            'parent': {'formatter': "minimal_format_memory_context_data_field"},
            'prevchild': {'formatter': "minimal_format_memory_context_data_field"},
            'firstchild': {'formatter': "minimal_format_memory_context_data_field"},
            'nextchild': {'formatter': "minimal_format_memory_context_data_field"},
        },
    },
    'NullIfExpr': {
        'fields': {
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
    'Param': {
        'fields':{
            'paramtypmod': {'visibility': "hide_invalid"},
            'paramcollid': {'visibility': "not_null"},
            'location': {'visibility': "never_show"},
        },
    },
    'PartitionBoundSpec': {
        'fields': {
            'everyGenList': {'formatter': 'format_everyGenList_node'},
            'location': {'visibility': "never_show"},
        },
    },
    'PartitionElem': {
        'fields': {
            'location': {'visibility': "never_show"},
        },
    },
    'PartitionSpec': {
        'fields': {
            'location': {'visibility': "never_show"},
        },
    },
    'Path': {
        'fields':{
            'parent': {'formatter': 'minimal_format_node_field'},
        },
    },
    'PlannerGlobal': {
        'fields':{
            'subroots': {'formatter': 'debug_minimal_format_node_list'},
        },
    },
    'PlannerInfo': {
        'fields':{
            'parent_root': {'formatter': 'minimal_format_node_field'},
            'subroots': {'formatter': 'debug_minimal_format_node_list'},
            # TODO: Broken. Need to make dumping these fields possible
            'simple_rel_array': {'visibility': 'never_show'},
            'simple_rte_array': {'visibility': 'never_show'},
            'upper_rels': {'formatter': 'minimal_format_node_field'},
            'upper_targets': {'formatter': 'minimal_format_node_field'},
        },
    },
    'PlanState': {
        'fields': {
            'lefttree': {
                  'field_type': 'tree_field',
                  'visibility': 'not_null',
                  'skip_tag': True
                },
            'righttree': {
                  'field_type': 'tree_field',
                  'visibility': 'not_null',
                  'skip_tag': True
                },
            'plan': { 'formatter': 'minimal_format_node_field', },
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
        },
    },
    'RangeVar': {
        'fields': {
            'catalogname': {'visibility': "not_null"},
            'schemaname': {'visibility': "not_null"},
            'location': {'visibility': "never_show"},
        },
    },
    'RestrictInfo': {
        'fields': {
            'parent_ec': {'formatter': 'minimal_format_node_field', },
            'scansel_cache': {'formatter': 'minimal_format_node_field', }
        },
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
    'TypeName': {
        'fields': {
            'typeOid': {'visibility': "not_null"},
            'typemod': {'visibility': "hide_invalid"},
            'location': {'visibility': "never_show"},
        },
    },
    'Var': {
        'fields':{
            'varno': {'formatter': "format_varno_field"},
            'vartypmod': {'visibility': "hide_invalid"},
            'varcollid': {'visibility': "not_null"},
            'varlevelsup': {'visibility': "not_null"},
            'varoattno': {'visibility': "hide_invalid"},
            'location': {'visibility': "never_show"},
        },
    },
    # Plan Nodes
    'Plan': {
        'fields': {
            'extParam': {'visibility': "not_null"},
            'allParam': {'visibility': "not_null"},
            'operatorMemKB': {'visibility': "not_null"},
            'lefttree': {
                  'field_type': 'tree_field',
                  'visibility': 'not_null',
                },
            'righttree': {
                  'field_type': 'tree_field',
                  'visibility': 'not_null',
                },
        },
    },

    # GPDB Specific Plan nodes
    'Motion': {
        'fields': {
            'hashFuncs': {'visibility': "not_null"},
            'segidColIdx': {'visibility': "not_null"},
            'numSortCols': {'visibility': "not_null"},
            'sortColIdx': {'visibility': "not_null"},
            'sortOperators': {'visibility': "not_null"},
            'nullsFirst': {'visibility': "not_null"},
            'senderSliceInfo': {'visibility': "not_null"},
        },
    },
    # GPDB Specific Partition related nodes
    'PartitionBy': {
        'fields': {
            'location': {'visibility': "never_show"},
        },
    },
    'PartitionRangeItem': {
        'fields': {
            'location': {'visibility': "never_show"},
        },
    },

}


StateNodes = []
for node in PlanNodes:
    StateNodes.append(node + "State")

JoinNodes = ['NestLoop', 'MergeJoin', 'HashJoin', 'Join', 'NestLoopState',
             'MergeJoinState', 'HashJoinState', 'JoinState']

recursion_depth = 0

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


def format_partition_values_spec(node, indent=0):
    retval = 'PartitionValuesSpec [location=%(location)s]' % {
        'location': node['location'],
    }

    retval += format_optional_node_list(node, 'partValues')

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

def is_old_style_list(l):
    try:
        x = l['head']
        return True
    except:
        return False

def format_oid_list(lst, indent=0):
    'format list containing Oid values directly (not warapped in Node)'

    # handle NULL pointer (for List we return NIL)
    if (str(lst) == '0x0'):
        return '(NIL)'

    # we'll collect the formatted items into a Python list
    tlist = []
    if is_old_style_list(lst):
        item = lst['head']

        # walk the list until we reach the last item
        while str(item) != '0x0':

            # get item from the list and just grab 'oid_value as int'
            tlist.append(int(item['data']['oid_value']))

            # next item
            item = item['next']
    else:
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

    if is_old_style_list(lst):
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
    else:
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

def max_depth_exceeded():
    global recursion_depth
    if recursion_depth >= DEFAULT_DISPLAY_METHODS['max_recursion_depth']:
        return True
    return False

def format_node(node, indent=0):
    'format a single Node instance (only selected Node types supported)'
    global recursion_depth
    recursion_depth += 1
    if max_depth_exceeded():
        recursion_depth -= 1
        if is_node(node):
            return "%s %s <max_depth_exceeded>" % (format_type(node['type']), str(node))
        else:
            return "%s <max_depth_exceeded>" % str(node)

    if str(node) == '0x0':
        return add_indent('(NULL)', indent)

    retval = ''

    if is_a(node, 'SortGroupClause'):
        node = cast(node, 'SortGroupClause')

        retval = format_sort_group_clause(node)

    elif is_a(node, 'TableLikeClause'):
        node = cast(node, 'TableLikeClause')

        retval = format_table_like_clause(node)

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

    elif is_a(node, 'GenericExprState'):
        node = cast(node, 'GenericExprState')

        retval = format_generic_expr_state(node)

    elif is_a(node, 'List'):
        node = cast(node, 'List')

        retval = format_node_list(node, 0, True)

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

    elif is_a(node, 'IndexElem'):
        node = cast(node, 'IndexElem')

        retval = format_index_elem(node)

    elif is_a(node, 'PartitionValuesSpec'):
        node = cast(node, 'PartitionValuesSpec')

        retval = format_partition_values_spec(node)

    elif is_a(node, 'Partition'):
        node = cast(node, 'Partition')

        retval = format_partition(node)

    elif is_a(node, 'String'):
        node = cast(node, 'Value')

        retval = 'String [%s]' % getchars(node['val']['str'])

    elif is_a(node, 'Integer'):
        node = cast(node, 'Value')

        retval = 'Integer [%s]' % node['val']['ival']

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
        node_formatter = PlanStateFormatter(node)
        retval += node_formatter.format()

    elif is_plannode(node):
        node_formatter = PlanStateFormatter(node)
        retval += node_formatter.format()

    elif is_statenode(node):
        node_formatter = PlanStateFormatter(node)
        retval += node_formatter.format()

    # TODO: NodeFormatter exceptions in these nodes
    elif is_a(node, "ColumnRef"):
        retval = format_type(type_str)

    else:
        node_formatter = NodeFormatter(node)
        retval += node_formatter.format()

    recursion_depth -= 1
    return add_indent(str(retval), indent)

def is_pathnode(node):
    for nodestring in PathNodes:
        if is_a(node, nodestring):
            return True

    return False

def is_plannode(node):
    for nodestring in PlanNodes:
        if is_a(node, nodestring):
            return True

    return False

def is_statenode(node):
    for nodestring in StateNodes:
        if is_a(node, nodestring):
            return True

    return False

def is_joinnode(node):
    for nodestring in JoinNodes:
        if is_a(node, nodestring):
            return True

    return False

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
    n = cast(n, 'Node')

    return (str(n['type']) == ('T_' + t))

def is_xpr(l):
    try:
        x = l['xpr']
        return True
    except:
        return False

def is_node(l):
    '''return True if the value looks like a Node (has 'type' field)'''
    if is_xpr(l):
        return True

    try:
        x = l['type']
        return True
    except:
        return False

def is_type(value, type_name, is_pointer):
    t = gdb.lookup_type(type_name)
    if(is_pointer):
        t = t.pointer()
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
    if is_node(node):
        node = cast(node, "Node")
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
    nodefields = [("Node", True), ("Expr", True)]
    type_name = str(node['type']).replace("T_", "")

    t = gdb.lookup_type(type_name)
    fields = []
    for v in t.values():
        for field, is_pointer in nodefields:
            if is_type(v, field, is_pointer):
                fields.append(v.name)

    return fields

def get_list_fields(node):
    listfields = [("List", True)]
    type_name = str(node['type']).replace("T_", "")

    t = gdb.lookup_type(type_name)
    fields = []
    for v in t.values():
        for field, is_pointer in listfields:
            if is_type(v, field, is_pointer):
                fields.append(v.name)
    return fields
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

def format_timeval_field(node, field):
    return "%s.%s" %(node[field]['tv_sec'], node[field]['tv_usec'])

def format_optional_node_field(node, fieldname, cast_to=None, skip_tag=False, print_null=False, indent=1):
    if cast_to != None:
        node = cast(node, cast_to)

    if str(node[fieldname]) != '0x0':
        node_output = format_node(node[fieldname])

        if skip_tag == True:
            return add_indent('%s' % node_output, indent, True)
        else:
            retval = '[%s] ' % fieldname
            if node_output.count('\n') > 0:
                node_output = add_indent(node_output, 1, True)
            retval += node_output
            return add_indent(retval , indent, True)
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

def format_everyGenList_node(node, fieldname, skip_tag=False, newLine=False, print_null=False, indent=1):
    retval = ''
    if str(node[fieldname]) != '0x0':
        genlist_strings = []
        if is_old_style_list(node[fieldname]):
            item = node[fieldname]['head']

            while str(item) != '0x0':

                listnode = cast(item['data']['ptr_value'], 'List')

                genlist_item = listnode['head']
                val = '['
                while str(genlist_item) != '0x0':
                    genlist_string = getchars(cast(genlist_item['data']['ptr_value'], 'char'))
                    val += genlist_string
                    # next item
                    genlist_item = genlist_item['next']
                    if str(genlist_item) != "0x0":
                       val += ' '
                val += ']'

                genlist_strings.append(val)

                # next item
                item = item['next']
        else:
            raise Exception("Tried to dump everyGenList using new style lists")

        if skip_tag == False:
            retval += '[%s]' % fieldname

        for item in genlist_strings:
            retval += add_indent(item, 1, True)

        retval = add_indent(retval, indent, True)
    elif print_null == True:
        retval += add_indent("[%s] (NIL)" % fieldname, indent, True)

    return retval


def format_gpmon_packet_field(node, fieldname, skip_tag=False, newLine=False, print_null=False, indent=1):
    return "<gpmon_packet>"

def minimal_format_node_field(node, fieldname, cast_to=None, skip_tag=False, print_null=False, indent=1):
    retval = ''
    if str(node[fieldname]) != '0x0':
        retval = add_indent("[%s] (%s)%s" % (fieldname, node[fieldname].type, node[fieldname]), indent, True)
    elif print_null == True:
        retval = add_indent("[%s] (NIL)" % fieldname, indent, True)

    return retval

def minimal_format_node_list(node, fieldname, cast_to=None, skip_tag=False, newLine=True, print_null=False, indent=1):
    retval = ''
    indent_add = 0
    if str(node[fieldname]) != '0x0':
        if skip_tag == False:
            retval += add_indent('[%s]' % fieldname, indent, True)
            indent_add = 1

        if newLine == True:
            retval += '\n'
            retval += '%s' % minimal_format_node_list_field(node, fieldname, cast_to, skip_tag, newLine, print_null, indent + indent_add)
        else:
            retval += ' %s' % minimal_format_node_list_field(node, fieldname, cast_to, skip_tag, newLine, print_null, 0)
    elif print_null == True:
        return add_indent("[%s] (NIL)" % fieldname, indent, True)

    return retval

def minimal_format_node_list_field(node, fieldname, cast_to=None, skip_tag=False, newLine=True, print_null=False, indent=1):
    'minimal format list containing Node values'
    if cast_to != None:
        lst = cast(node[fieldname], cast_to)
    else:
        lst = node[fieldname]

    # we'll collect the formatted items into a Python list
    tlist = []

    if is_old_style_list(lst):
        item = lst['head']

        # walk the list until we reach the last item
        while str(item) != '0x0':
            lstnode = cast(item['data']['ptr_value'], 'Node')
            nodetype = get_base_node_type(lstnode)
            lstnode = cast(lstnode, nodetype)

            val = "(%s)%s" % (lstnode.type, node[fieldname])
            # append the formatted Node to the result list
            tlist.append(val)

            # next item
            item = item['next']
    else:
        for col in range(0, lst['length']):
            element = lst['elements'][col]
            lstnode = cast(item['data']['ptr_value'], 'Node')
            nodetype = get_base_node_type(lstnode)
            lstnode = cast(lstnode, nodetype)

            val = "(%s)%s" % (lstnode.type, node[fieldname])

            tlist.append(val)

    if newLine:
        retval = "\n".join([str(t) for t in tlist])
    else:
        retval = str(tlist)

    return add_indent(retval, indent)


def minimal_format_memory_context_data_field(node, fieldname, cast_to=None, skip_tag=False, print_null=False, indent=1):
    retval = ''
    if str(node[fieldname]) != '0x0':
        retval = add_indent("[%s] (%s)%s [name=%s]" % (fieldname, node[fieldname].type, node[fieldname], format_string_pointer_field(node[fieldname], 'name')), indent, True)
    elif print_null == True:
        retval = add_indent("[%s] (NIL)" % fieldname, indent, True)

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

def debug_format_optional_node_field(node, fieldname, cast_to=None, skip_tag=False, print_null=False, indent=1):
    print("debug_format_optional_node_field: %s[%s]: cast_to=%s skip_tag=%s print_null=%s, indent=%s" % (get_base_node_type(node), fieldname,
        cast_to, skip_tag, print_null, indent))
    ret = format_optional_node_field(node, fieldname, cast_to, skip_tag, True, indent)
    print(ret)
    return ret

def debug_format_optional_node_list(node, fieldname, cast_to=None, skip_tag=False, newLine=True, print_null=False, indent=1):
    print("debug_format_optional_node_list: %s[%s]: %s" % (get_base_node_type(node), fieldname,
        format_optional_node_list(node, fieldname, cast_to, skip_tag, newLine, print_null, indent)))
    return format_optional_node_list(node, fieldname, cast_to, skip_tag, newLine, print_null, indent)

def debug_format_optional_oid_list(node, fieldname, skip_tag=False, newLine=False, print_null=False, indent=1):
    print("debug_format_optional_oid_list: %s[%s]: %s" % (get_base_node_type(node), fieldname,
        format_optional_oid_list(node, fieldname, skip_tag, newLine, print_null, indent)))
    return format_optional_oid_list(node, fieldname, newLine, skip_tag, print_null, indent)

def debug_minimal_format_node_list(node, fieldname, cast_to=None, skip_tag=False, print_null=False, indent=1):
    print("debug_minimal_format_node_list: %s[%s]: cast_to=%s skip_tag=%s print_null=%s, indent=%s" % (get_base_node_type(node), fieldname,
        cast_to, skip_tag, print_null, indent))
    ret = minimal_format_node_list(node, fieldname, cast_to, skip_tag, True, indent)
    print(ret)
    return ret


class NodeFormatter(object):
    # Basic node information
    _node = None
    __node_type = None
    __type_str = None
    __parent_node = None

    # String representations of individual fields in node
    __all_fields = None
    _regular_fields = None
    __node_fields = None
    __list_fields = None
    __tree_fields = None
    _ignore_field_types = None

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
        self.__list_types = [("List",True)]
        # Postgres
        #self.__node_types = [("Node",True), ("Expr", True), ("FromExpr", True), ("OnConflictExpr", True), ("RangeVar", True), ("TypeName", True), ("ExprContext", True), ("MemoryContext", True), ("CollateClause", True), ("struct SelectStmt", True), ("Alias", True), ("struct Plan", True)]
        # GPDB 4.x
        self.__node_types = [("Node",True), ("Expr", True), ("FromExpr", True), ("RangeVar", True), ("TypeName", True), ("ExprContext", True), ("MemoryContext", True), ("struct SelectStmt", True), ("Alias", True), ("struct Plan", True)]

        # TODO: Make the node lookup able to handle inherited types(like Plan nodes)
        if typecast == None:
            typecast = get_base_node_type(node)
        self.__type_str = typecast
        self._node = cast(node, self.type)

        # Get methods for display
        self.__default_display_methods = DEFAULT_DISPLAY_METHODS
        self.__default_regular_visibility = ALWAYS_SHOW
        self.__default_list_visibility = NOT_NULL
        self.__default_node_visibility = NOT_NULL
        self.__default_skip_tag = False
        self.__formatter_overrides = FORMATTER_OVERRIDES.get(self.type)
        #print("NodeFormatter:", self.type)

    def is_child_node(self):
        t = gdb.lookup_type(self.type)
        first_field = t.values()[0]

        if first_field.name == "type":
            return False
        elif first_field.name == "xpr":
            return False
        elif first_field.name == "xprstate":
            return False

        return True

    @property
    def parent_node(self):
        if self.__parent_node == None:
            if self.is_child_node():
                t = gdb.lookup_type(self.type)
                first_field = t.values()[0]

                self.__parent_node = NodeFormatter(self._node, str(first_field.type))
        return self.__parent_node


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

        if field in self.regular_fields:
            return globals()[self.__default_display_methods['regular_fields']]
        elif field in self.node_fields:
            return globals()[self.__default_display_methods['node_fields']]
        elif field in self.list_fields:
            return globals()[self.__default_display_methods['list_fields']]
        elif field in self.tree_fields:
            return globals()[self.__default_display_methods['tree_fields']]

        raise Exception("Did not find a display method for %s[%s]" % (self.type, field))


    def get_display_mode(self, field):
        # If the global 'show_hidden' is set, then this command shal always
        # return ALWAYS_SHOW
        if self.__default_display_methods['show_hidden'] == True:
            return ALWAYS_SHOW

        override_string = self.get_field_override(field, 'visibility')
        if override_string != None:
            return override_string

        if field in self.regular_fields:
            return self.__default_regular_visibility
        if field in self.list_fields:
            return self.__default_list_visibility
        if field in self.node_fields:
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
                skip = False

                field = t.values()[index]
                # TODO: should the ability to ignore fields entirely exist at all?
                #       This seems to conflict with the visibility settings
                # Fields that are to be ignored
                if self._ignore_field_types is not None:
                    for tag, is_pointer in self._ignore_field_types:
                        if self.is_type(field, tag, is_pointer):
                            skip = True

                if index == 0:
                    # The node['type'] field is just a tag that we already know
                    if field.name == "type":
                        skip = True
                    # The node['xpr'] field is just a wrapper around node['type']
                    elif field.name == "xpr":
                        skip = True
                    elif field.name == "xprstate":
                        skip = True
                    elif self.is_child_node():
                        skip = True
                if skip:
                    continue

                self.__all_fields.append(field.name)

        return self.__all_fields

    # TODO: any given field should ONLY be in one of these lists, so I need
    # to decide on an order of precidence for these lists
    @property
    def list_fields(self):
        if self.__list_fields == None:
            self.__list_fields = []

            for f in self.fields:
                # Honor overrides before all else
                override_string = self.get_field_override(f, 'field_type')
                if override_string != None:
                    if override_string == 'list_field':
                        self.__list_fields.append(f)
                    else:
                        continue

                v = self._node[f]
                for field, is_pointer in self.__list_types:
                    if self.is_type(v, field, is_pointer):
                        self.__list_fields.append(f)

        return self.__list_fields

    @property
    def node_fields(self):
        if self.__node_fields == None:
            self.__node_fields = []

            for f in self.fields:
                override_string = self.get_field_override(f, 'field_type')
                if override_string != None:
                    if override_string == 'node_field':
                        self.__node_fields.append(f)
                    else:
                        continue

                v = self._node[f]
                for field, is_pointer in self.__node_types:
                    if self.is_type(v, field, is_pointer):
                        self.__node_fields.append(f)

                if is_node(v):
                    if f not in self.list_fields:
                        self.__node_fields.append(f)

        return self.__node_fields

    @property
    def tree_fields(self):
        if self.__tree_fields == None:
            self.__tree_fields = []
            for f in self.fields:
                override_string = self.get_field_override(f, 'field_type')
                if override_string != None:
                    if override_string == 'tree_field':
                        self.__tree_fields.append(f)
                    else:
                        continue

        return self.__tree_fields

    # TODO: Regular fields should be able to be overridden to other data types too
    @property
    def regular_fields(self):
        if self._regular_fields == None:
            self._regular_fields = []

            self._regular_fields = [field for field in self.fields if field not in self.list_fields + self.node_fields + self.tree_fields]

        return self._regular_fields

    # TODO: should this be a class method?
    # TODO: This is definitely broken, as lookup_type behaves differently
    #       for different versions of gdb. Need to figure out a portable
    #       way to do this
    def is_type(self, value, type_name, is_pointer):
        t = gdb.lookup_type(type_name)
        if(is_pointer):
            t = t.pointer()
        return (str(value.type) == str(t))
        # This doesn't work for list types for some reason...
        # return (gdb.types.get_basic_type(value.type) == gdb.types.get_basic_type(t))

    def field_datatype(self, field):
        return gdb.types.get_basic_type(self._node[field].type)

    def format(self, prefix=None):
        retval = ''
        if prefix != None:
            retval = prefix
        retval += self.type + ' '
        newline_padding_chars = len(retval)
        formatted_fields = self.format_all_regular_fields(newline_padding_chars+1)

        fieldno = 1
        for field in formatted_fields:
            retval += field
            if fieldno < len(formatted_fields):
                retval += '\n' + ' ' * newline_padding_chars
            fieldno += 1

        retval += self.format_complex_fields()

        retval += self.format_tree_nodes()

        return retval

    def format_regular_fields(self, newline_padding_chars):
        # TODO: get this value from config file
        max_regular_field_chars = 140
        retval = "["

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
                if self._node[field] == empty_value:
                    continue

            # Some fields are initialized to -1 if they are not used
            if display_mode == HIDE_INVALID:
                field_datatype = self.field_datatype(field)
                empty_value = gdb.Value(-1).cast(field_datatype)
                if self._node[field] == empty_value:
                    continue

            value = self.format_regular_field(field)


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

    def format_regular_field(self, field):
        display_method = self.get_display_method(field)
        return display_method(self._node, field)

    def format_complex_fields(self):
        retval = ""
        if self.is_child_node():
            retval += self.parent_node.format_complex_fields()

        for field in self.fields:
            if field in self.regular_fields:
                continue
            if field in self.tree_fields:
                continue
            retval += self.format_complex_field(field)

        return retval

    def format_complex_field(self, field):
        display_mode = self.get_display_mode(field)
        print_null = False
        if display_mode == NEVER_SHOW:
            return ""
        elif display_mode == ALWAYS_SHOW:
            print_null = True

        skip_tag = self.is_skip_tag(field)

        display_method = self.get_display_method(field)
        return display_method(self._node, field, skip_tag=skip_tag, print_null=print_null)

    def format_all_regular_fields(self, offset):
        formatted_fields = []
        if self.parent_node != None:
            formatted_fields += self.parent_node.format_all_regular_fields(offset)

        formatted_fields.append(self.format_regular_fields(offset))
        return formatted_fields


    def ignore_type(self, field, is_pointer):
        if self._ignore_field_types is None:
            self._ignore_field_types = []
        self._ignore_field_types.append((field, is_pointer))

        # reset list of all fields
        self.__list_fields = None
        self._regular_fields = None
        self.__all_fields = None

    def format_tree_nodes(self):
        retval = ""
        for field in self.tree_fields:
            retval += self.format_complex_field(field)

        if retval == "" and self.is_child_node():
            retval += self.parent_node.format_tree_nodes()

        return retval

class PlanStateFormatter(NodeFormatter):
    def format(self):
        return super().format(prefix='-> ')

class PgPrintCommand(gdb.Command):
    "print PostgreSQL structures"

    def __init__(self):
        super(PgPrintCommand, self).__init__("pgprint", gdb.COMMAND_SUPPORT,
                                             gdb.COMPLETE_NONE, False)

    def invoke(self, arg, from_tty):
        global recursion_depth

        arg_list = gdb.string_to_argv(arg)
        if len(arg_list) != 1:
            print("usage: pgprint var")
            return
        recursion_depth = 0

        l = gdb.parse_and_eval(arg_list[0])

        if not is_node(l):
            print("not a node type")

        print(format_node(l))


PgPrintCommand()
