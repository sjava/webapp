#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, url_for, render_template, session, redirect, g, abort
from flask_bootstrap import Bootstrap
from flask_json import FlaskJSON, JsonError, json_response, as_json
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import Required, ValidationError
from py2neo import Graph, Node, authenticate
import time
import os
import apsw
import configparser
import simplejson as json
from funcy import re_all, re_find, merge_with, lmap, all, any
from functools import reduce
from werkzeug.contrib.fixers import ProxyFix
from operator import itemgetter
import tools as myTools

app = Flask(__name__)
FlaskJSON(app)
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config[
    'SECRET_KEY'] = "\x84\x92\xe0=_\x1ea`h!Q\xf6Q\xd0\xb8\x1bGG\x84\x197\x1b\xe6\x1f"

config = configparser.ConfigParser()
config.read(os.path.expanduser('~/.weihu/config.ini'))
neo4j_username = config.get('neo4j', 'username')
neo4j_password = config.get('neo4j', 'password')
authenticate('61.155.48.36:7474', neo4j_username, neo4j_password)
graph = Graph("http://61.155.48.36:7474/db/data")

database = 'weihu.db'


def get_db():
    db = getattr(g, '_database', None)
    if not db:
        db = g._database = apsw.Connection(database)
    return db


#  @app.teardown_appcontext
#  def close_connection(exception):
    #  db = getattr(g, '_database', None)
    #  if db:
    #  db.close()


class TaskForm(Form):
    task = TextAreaField(label='增加割接任务', validators=[Required()])
    submit = SubmitField('保存')

    def validate_task(form, field):
        sw_model = re_all(r'_sw:(?:\d+\.){3}\d+:(\w+)', field.data)
        bras = re_all(r'_bas:(?:\d+\.){3}\d+:(\w+):\d+', field.data)
        area = re_find(r'area[:,：](\S+)', field.data)
        if not area:
            raise ValidationError('请填写属地信息')
        if not all(lambda x: x.lower() in ['s85', 's89', 's8905e', 's93', 't64g'], sw_model):
            raise ValidationError('switch 型号不正确')
        if not all(lambda x: x.lower() in ['m6k', 'me60'], bras):
            raise ValidationError('bras 型号不正确')


@app.route('/')
def sw_groups():
    cmd = """
    match(s:Switch)-->(g:Group)-->(i:Inf{state:'up'})
    where i.desc=~"(?i).*(ut|ME60|M6000|-BAS-|-B-|-BAS\\\\.).*" or g.desc=~"(?i).*(ut|ME60|M6000|-BAS-|-B-|-BAS\\\\.).*"
    with s as switch,g as group,sum(i.bw) as zdw,sum(i.inTraffic) as in,sum(i.outTraffic) as out
    return switch.ip,group.name,group.desc,zdw,in/zdw as xiaxing,out/zdw as shangxing,switch.area order by xiaxing desc"""
    nodes = graph.cypher.execute(cmd)
    rslt = [dict(ip=x[0], name=x[1], desc=x[2], zdw=int(x[3]),
                 xiaxing=format(x[4], '.2%'), shangxing=format(x[5], '.2%'), area=x[6])
            for x in nodes]
    temp = graph.cypher.execute(
        "match(:Switch)-->(i:Inf) where i.state='up' return max(i.updated)")
    collTime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(temp[0][0] / 1000))
    return render_template('index.html', collTime=collTime, rslt=rslt)


@app.route('/ports')
def sw_ports():
    cmd = r"""
    match(s:Switch)-->(g:Group)-->(i:Inf{state:'up'})
    where i.desc=~"(?i).*(ut|ME60|M6000|-BAS-|-B-|-BAS\\.).*"
    return s.ip,i.name,i.desc,i.bw,i.inTraffic/i.bw as in,i.outTraffic/i.bw as out ,s.area order by in desc"""
    nodes = graph.cypher.execute(cmd)
    rslt = [dict(ip=x[0], name=x[1], desc=x[2], bw=int(x[3]),
                 xiaxing=format(x[4], '.2%'), shangxing=format(x[5], '.2%'), area=x[6])
            for x in nodes]
    temp = graph.cypher.execute(
        "match (s:Switch)-->(i:Inf) where i.state='up' return max(i.updated)")
    collTime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(temp[0][0] / 1000))
    return render_template('ports.html', collTime=collTime, rslt=rslt)


@app.route('/olt_groups')
def olt_groups():
    cmd = """
    match (n:Olt)-->(g:Group)-->(i:Inf)
    where i.state='up'
    with n,g,sum(i.bw) as bw,sum(i.inTraffic) as in,sum(i.outTraffic) as out
    return n.ip,g.name,g.desc,bw,in/bw as xiaxing,out/bw as shangxing ,n.area order by xiaxing desc
    """
    rslt = graph.cypher.execute(cmd)
    rslt = [dict(ip=x[0], name=x[1], desc=x[2], bw=int(x[3]),
                 xiaxing=format(x[4], '.2%'), shangxing=format(x[5], '.2%'), area=x[6])
            for x in rslt]
    temp = graph.cypher.execute("match(:Olt)-->(i:Inf) return max(i.updated)")
    collTime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(temp[0][0] / 1000))
    return render_template('olt_groups.html', collTime=collTime, rslt=rslt)


@app.route('/olt_ports')
def olt_ports():
    cmd = """
    match (n:Olt)-->(i:Inf)
    where i.state='up'
    return n.ip,i.name,i.desc,i.bw,i.inTraffic/i.bw as xiaxing,i.outTraffic/i.bw as shangxing,n.area
    order by xiaxing desc
    """
    rslt = graph.cypher.execute(cmd)
    rslt = [dict(ip=x[0], name=x[1], desc=x[2], bw=int(x[3]),
                 xiaxing=format(x[4], '.2%'), shangxing=format(x[5], '.2%'), area=x[6])
            for x in rslt]
    temp = graph.cypher.execute("match(:Olt)-->(i:Inf) return max(i.updated)")
    collTime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(temp[0][0] / 1000))
    return render_template('olt_ports.html', collTime=collTime, rslt=rslt)


@app.route('/bingfa')
def bingfa():
    cmd = """
    match (b:Bras)-->(c:Card)
    return b.ip,c.slot,c.peakUsers,c.peakTime,c.updated
    order by c.peakUsers desc"""
    temp = graph.cypher.execute(cmd)
    rslt = [dict(ip=x[0], slot=x[1], peakUsers=x[2], peakTime=x[3])
            for x in temp]
    temp1 = graph.cypher.execute(
        "match (b:Bras)-->(c:Card) return max(c.updated)")
    collTime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(temp1[0][0] / 1000))
    return render_template('bingfa.html', collTime=collTime, rslt=rslt)


@app.route('/geji', methods=['GET', 'POST'])
def geji():
    cursor = get_db().cursor()
    task = cursor.execute("select * from task order by id desc")
    return render_template('geji.html', task=task)


@app.route('/task_add', methods=['GET', 'POST'])
def task_add():
    cursor = get_db().cursor()
    form = TaskForm()
    if form.validate_on_submit():
        task = form.task.data.lower()
        form.task.data = None
        old_sw_ip, old_sw_model = re_find(
            r'old_sw:((?:\d+\.){3}\d+):(\w+)', task)
        area = re_find(r'area[:,：](\S+)', task)
        cursor.execute(
            "insert into task(ip,desc,area) values(?,?,?)", (old_sw_ip, task, area))
        return redirect(url_for('geji'))
    return render_template('task_add.html', form=form)


@app.route('/task/<int:id>')
def task(id):
    cursor = get_db().cursor()
    rslt = cursor.execute("select desc from task where id=?", [id])
    rslt = rslt.fetchall()
    if rslt:
        task = rslt[0]
    #  return render_template('task.html', task=task)
    return json_response(task=task[0])


@app.route('/check_before/<int:id>')
def check_before(id):
    cursor = get_db().cursor()
    rslt = cursor.execute("select * from task where id=?", [id])
    rslt = rslt.fetchall()
    if rslt:
        task = rslt[0]
        if task[3] and task[4]:
            ports = json.loads(task[3])
            vlan_users = json.loads(task[4])
        else:
            old_sw_ip, old_sw_model = re_find(
                r'old_sw:((?:\d+\.){3}\d+):(\w+)', task[2])
            bras = re_all(r'old_bas:((?:\d+\.){3}\d+):(\w+):(\d+)', task[2])
            ports = myTools.get_ports(old_sw_ip, old_sw_model)
            vlans = myTools.get_vlans(old_sw_ip, old_sw_model)
            #  temp = myTools.get_vlan_users(bras)
            #  temp = [x[1] for x in temp if x[1]]
            #  temp1 = reduce(lambda x, y: merge_with(sum, x, y), temp)
            temp1 = myTools.get_vlan_usersP(bras)
            vlan_users = lmap(lambda x: (x, temp1.get(x, 0)), sorted(vlans[1]))
            cursor.execute("update task set old_ports=?,old_vlans=? where id=?",
                           (json.dumps(ports), json.dumps(vlan_users), id))
    else:
        abort(404)
    return render_template('before.html', ports=ports, vlan_users=vlan_users)


@app.route('/check_after/<int:id>')
def check_after(id):
    cursor = get_db().cursor()
    rslt = cursor.execute("select * from task where id=?", [id])
    rslt = rslt.fetchall()
    if not rslt:
        abort(404)
    task = rslt[0]
    if task[3] is None or task[4] is None:
        #  abort(404)
        return render_template('error.html')
    before_vlan_users = dict(json.loads(task[4]))
    new_sw_ip, new_sw_model = re_find(
        r'new_sw:((?:\d+\.){3}\d+):(\w+)', task[2])
    bras = re_all(r'new_bas:((?:\d+\.){3}\d+):(\w+):(\d+)', task[2])
    ports = myTools.get_ports(new_sw_ip, new_sw_model)
    vlans = myTools.get_vlans(new_sw_ip, new_sw_model)
    #  temp = myTools.get_vlan_usersP(bras)
    #  temp = [x[1] for x in temp if x[1]]
    #  temp1 = reduce(lambda x, y: merge_with(sum, x, y), temp)
    temp1 = myTools.get_vlan_usersP(bras)
    after_vlan_users = dict(
        lmap(lambda x: (x, temp1.get(x, 0)), sorted(vlans[1])))
    check_vlan_users = [[x, before_vlan_users.get(x), after_vlan_users.get(x, 'not find')]
                        for x in before_vlan_users.keys()]
    cursor.execute("update task set new_ports=?,new_vlans=? where id=?",
                   (json.dumps(ports), json.dumps(check_vlan_users), id))
    return redirect(url_for('show_check_result', id=id))


@app.route('/show_check_result/<int:id>')
def show_check_result(id):
    cursor = get_db().cursor()
    rslt = cursor.execute(
        "select new_ports,new_vlans from task where id=?", [id])
    rslt = rslt.fetchall()
    if not rslt:
        abort(404)
    rslt = rslt[0]
    ports = json.loads(rslt[0])
    vlan_users = json.loads(rslt[1])
    vlan_users = sorted(vlan_users, key=itemgetter(0))
    return render_template('after.html', ports=ports, vlan_users=vlan_users)

#  @app.route('/task_del/<int:id>')
#  def task_del(id):
    #  cursor = get_db().cursor()
    #  cursor.execute("delete from task where id=?", (id,))
    #  return redirect(url_for('geji'))


@app.route('/olt_xunjian', methods=['GET'])
def olt_xunjian():
    singleMainCard = graph.cypher.execute(
        "match(n:Olt) where n.mainCard<2 return n.ip as ip,n.area as area,n.hostname as name order by area")
    powerInfo = graph.cypher.execute(
        "match(n:Olt) where n.powerInfo='alarm' return n.ip as ip,n.area as area,n.hostname as name order by area")
    return render_template('olt_xunjian.html',  singleMainCard=singleMainCard, powerInfo=powerInfo)


@app.route('/sw_xunjian', methods=['GET'])
def sw_xunjian():
    singleMainCard = graph.cypher.execute(
        "match(s:Switch) where s.mainCard<2 and s.snmpState='normal' return s.ip as ip,s.area as area,s.hostname as name order by area")
    powerInfo = graph.cypher.execute(
        "match(s:Switch) where s.powerInfo<2 and s.snmpState='normal' return s.ip as ip,s.area as area,s.hostname as name order by area")
    stmt = """
    match(s:Switch)-->(g:Group)
    where g.mode <> 'yes'
    return
    s.area as area,
    s.ip as ip,
    s.hostname as hostname,
    g.name as name,
    g.desc as desc
    order by area
    """
    lacp = graph.cypher.execute(stmt)
    return render_template('sw_xunjian.html', lacp=lacp, singleMainCard=singleMainCard, powerInfo=powerInfo)

app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
