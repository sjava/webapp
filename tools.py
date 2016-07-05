#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/home/zyb/weihu1')
from device.bras import M6k, ME60
from device.switch import S85, S89, S8905E, S93, T64
from funcy import partial, lmap, merge_with
from multiprocess import Pool
from functools import reduce


def _model(funcs, device):
    def no_model(**kw): return ('fail', None, kw['ip'])
    model = device.pop('model')
    return funcs.get(model, no_model)(**device)


def get_ports(ip, model):
    funcs = {'s85': S85.get_ports,
             't64g': T64.get_ports,
             's89': S89.get_ports,
             's8905e': S8905E.get_ports,
             's93': S93.get_ports}
    _get_ports = partial(_model, funcs)
    return _get_ports(dict(ip=ip, model=model))


def get_vlans(ip, model):
    funcs = {'s85': S85.get_vlans,
             't64g': T64.get_vlans,
             's89': S89.get_vlans,
             's8905e': S8905E.get_vlans,
             's93': S93.get_vlans_a}
    _get_vlans = partial(_model, funcs)
    return _get_vlans(dict(ip=ip, model=model))


def get_vlan_users(bras):
    def _get_vlan_users(bas):
        funcs = {'m6k': M6k.get_vlan_users,
                 'me60': ME60.get_vlan_users}
        _gvu = partial(_model, funcs)
        return _gvu(bas)

    bras = [dict(ip=x[0], model=x[1], inf=x[2])
            for x in bras]
    rslt = lmap(_get_vlan_users, bras)
    return rslt


def get_vlan_usersP(bras):
    def _get_vlan_users(bas):
        funcs = {'m6k': M6k.get_vlan_users,
                 'me60': ME60.get_vlan_users}
        _gvu = partial(_model, funcs)
        return _gvu(bas)

    bras = [dict(ip=x[0], model=x[1], inf=x[2])
            for x in bras]
    pool = Pool(len(bras))
    temp = pool.map(_get_vlan_users, bras)
    pool.close()
    pool.join()
    temp = [x[1] for x in temp if x[1]]
    rslt = reduce(lambda x, y: merge_with(sum, x, y), temp)
    return rslt
