import datetime
import json
import logging
import time
from _md5 import md5
from decimal import Decimal
from io import BytesIO

import pandas as pd
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from hospital_client.models import ClientUser, Menu, Role, Permission, Company, Herbs, Prescription, PresDetails, Order
from requires import generate_code
from requires.authorityControl import get_menu_html
from requires.handle import DateEncoder, string_to_list, query_dict2python_dict, md5_creat_password
from requires.prescriptionServices import upload_prescription, cancel
logger = logging.getLogger('log')


def login(request):
    err_msg = {}
    if request.method == 'POST':
        # POST 请求,获取用户输入的用户名和密码
        username = request.POST.get('username')
        password = request.POST.get('password')
        verify_code = request.POST.get('code')
        if cache.get('verify_code') == verify_code.upper():
            if username != 'whiteadmin':
                user = ClientUser.objects.filter(username=username, password=password).first()
                if user:
                    request.session["client_is_login"] = True
                    request.session['client_user_name'] = user.username
                    request.session.set_expiry(0)  # 关闭浏览器就清掉session
                    if user.is_disabled > 0:
                        return redirect(reverse('hospital_client:index'))
                    else:
                        err_msg['uperror'] = '该用户已停用,请联系管理员！'
                else:
                    err_msg["uperror"] = '用户名或密码错误！'
            else:
                if password == md5('whiteadmin'.encode('utf-8')).hexdigest():
                    request.session['client_user_name'] = 'whiteadmin'
                    request.session.set_expiry(0)
                    return render(request, 'hospital/white_admin_index.html')
                else:
                    err_msg["uperror"] = '用户名或密码错误！'
        else:
            err_msg['cerror'] = "验证码错误或已过期！"
    return render(request, 'hospital/login.html', err_msg)


def change_verify_code(request):
    im = generate_code.gene_code()
    fp = BytesIO()
    im[0].save(fp, 'png')
    cache.set('verify_code', im[1], 60)
    return HttpResponse(fp.getvalue(), content_type='image/png')


def index(request):
    is_login = request.session.get('client_is_login')
    username = request.session.get('client_user_name')
    if not is_login:
        """如果没有登录则跳转至登录页面"""
        return redirect(reverse('hospital_client:login'))
    user = ClientUser.objects.get(username=username)
    user.login_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user.save()
    permission_item_list = list(user.role.values('permissions__url',
                                                 'permissions__title',
                                                 'permissions__per_id',
                                                 'permissions__menu_id').distinct())
    permission_list = []  # 用户权限url列表
    permission_menu_list = []  # 用户权限url所属菜单列表

    for item in permission_item_list:
        if item['permissions__menu_id']:
            temp = {"title": item['permissions__title'],
                    "url": item["permissions__url"],
                    "menu_id": item["permissions__menu_id"],
                    'per_id': item["permissions__per_id"]}
            permission_list.append(temp)
            if item['permissions__menu_id'] in permission_menu_list:
                continue
            else:
                permission_menu_list.append(item['permissions__menu_id'])
    menu_list = list(Menu.objects.filter(id__in=permission_menu_list).values('id', 'title', 'icon'))
    # 注：session在存储时，会先对数据进行序列化，因此对于Queryset对象写入session， 加list()转为可序列化对象
    # print(permission_list)
    # print(menu_list)
    menu_html = get_menu_html(menu_list, permission_data=permission_list)
    context = {'name': user.username, 'menu_html': menu_html}
    # print(context)
    return render(request, 'hospital/index.html', context)


@csrf_exempt
def menu_manage(request, type):
    if type == 'menuAdd':
        context = {}
        if request.method == 'POST':
            menu = Menu()
            menu.title = request.POST.get('menuname')
            menu.icon = request.POST.get('menuicon')
            menu.menu_type = request.POST.get('menutype')
            menu.parent_id = request.POST.get('parentMenu')
            try:
                menu.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type='application/json')
        return render(request, 'hospital/systemManage/menu/menu_add.html')
    if type == 'parentMenu':
        parent_menu = Menu.objects.exclude(parent_id__gt=1)
        json_menus = serializers.serialize('json', parent_menu)
        return HttpResponse(json_menus)
    if type == 'menuEdit':
        context = {}
        if request.method == 'POST':
            menu = Menu.objects.get(id=request.POST.get('menuid'))
            menu.title = request.POST.get('menuname')
            menu.icon = request.POST.get('menuicon')
            menu.menu_type = request.POST.get('menutype')
            menu.parent_id = request.POST.get('parentMenu')
            try:
                menu.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type='application/json')
        return render(request, 'hospital/systemManage/menu/menu_add.html')
    if type == 'menuDelete':
        context = {}
        try:
            Menu.objects.get(id=request.POST.get('delData')).delete()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'home':
        return render(request, 'hospital/systemManage/menu/menu_manage.html')


def home(request):
    return render(request, 'hospital/home.html')


@csrf_exempt
def update_pass(request):
    context = {}
    if request.method == 'POST':
        user = ClientUser.objects.get(name=request.POST.get('uName'))
        # print(user.password)
        # print(request.POST.get('prePassword'))
        if user.password == request.POST.get('prePassword'):
            user.password = request.POST.get('newPassword')
            try:
                user.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
        else:
            context['status'] = 'fail'
            context['message'] = '原密码不正确！'
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    return render(request, 'hospital/systemManage/user/update_pass.html')


def logout(request):
    request.session.flush()
    return redirect(reverse('hospital_client:login'))


@csrf_exempt
def table_data(request, type):
    lis = []
    data_count = 0
    if type == 'menu_table':
        menuname = request.GET.get('menuname')
        menutype = request.GET.get('menutype')
        q1 = Q()
        q1.connector = 'AND'
        if menuname:
            q1.children.append(('title', menuname))
        if menutype:
            q1.children.append(('menu_type', menutype))
        if q1.children:
            menu_datas = Menu.objects.filter(q1)
            data_count += menu_datas.count()
            lis = list(menu_datas.values())
            for i in range(len(lis)):
                if lis[i]['parent_id']:
                    lis[i]['parent_id'] = menu_datas[i].parent.title
                else:
                    lis[i]['parent_id'] = ''
        else:
            menu_datas = Menu.objects.all()
            data_count += menu_datas.count()
            lis = list(menu_datas.order_by('id').values())
            # print(menu_datas)
            # print(lis)
            for i in range(len(lis)):
                if lis[i]['parent_id']:
                    lis[i]['parent_id'] = menu_datas[i].parent.title
                else:
                    lis[i]['parent_id'] = ''
    if type == 'user_table':
        username = request.GET.get('username')
        role = request.GET.get('role')
        last_login_start = request.GET.get('lastLoginStart')
        last_login_end = request.GET.get('lastLoginEnd')
        q1 = Q()
        q1.connector = 'AND'
        if username:
            q1.children.append(('username', username))
        if role:
            q1.children.append(('role', role))
        if last_login_start and last_login_end:
            q1.children.append(('login_time__range', (last_login_start, last_login_end)))
        # print(query_dict)
        if q1.children:
            user_datas = ClientUser.objects.filter(q1)
            data_count += user_datas.count()
            lis = list(user_datas.values())
            for i in range(len(lis)):
                lis[i]['role'] = list(user_datas[i].role.all().values('role_name'))[0]['role_name']
                lis[i]['company_id_id'] = user_datas[i].company_id.name
        else:
            user_datas = ClientUser.objects.all()
            data_count += user_datas.count()  # 数据总数
            lis = list(user_datas.values())
            for i in range(len(lis)):       # 级联数据
                lis[i]['role'] = list(user_datas[i].role.all().values('role_name'))[0]['role_name']
                lis[i]['company_id_id'] = user_datas[i].company_id.name
            # print(lis)
    elif type == 'role_table':
        roleName = request.GET.get('rolename')
        if roleName:
            role_datas = Role.objects.filter(role_name=roleName)
            data_count += role_datas.count()
            lis = list(role_datas.valus())
        else:
            data_count += Role.objects.all().count()  # 数据总数
            lis = list(Role.objects.all().order_by('id').values())
    elif type == 'goods_table':
        username = request.session.get('client_user_name')
        # print(username)
        company = ClientUser.objects.get(username=username).company_id.id
        drugs_code = request.GET.get('drugsCode')
        drugs_name = request.GET.get('drugsName')
        drugs_status = request.GET.get('drugsStatus')
        drugs_type = request.GET.get('drugsType')
        company_search = request.GET.get('companySearch')
        is_hand_edit = request.GET.get('isHandEdit')
        q2 = Q()
        q3 = Q()
        q2.connector = 'AND'  # q2对象表示‘OR’关系，也就是说q2下的条件都要满足‘OR’
        q3.connector = 'OR'
        if drugs_name:
            keys = ['drugs_name', 'short_code', 'alias1', 'alias2', 'alias3', 'alias4',
                    'alias5', 'alias6', 'alias7', 'alias8', 'alias9', 'alias10']
            for key in keys:
                new_key = key + '__contains'
                q3.children.append((new_key, drugs_name))
        if drugs_code:
            q2.children.append(('drugs_code', drugs_code))
        if drugs_status:
            q2.children.append(('status', drugs_status))
        if drugs_type:
            q2.children.append(('drugs_type', drugs_type))
        if company_search:
            q2.children.append(('company_id', company_search))
        if is_hand_edit:
            q2.children.append(('isnot_handedit', is_hand_edit))
        if (q2 & q3).children:
            drugs_datas = Herbs.objects.filter(q2 & q3)
            search_company_name = Company.objects.get(id=company_search).name
            data_count += drugs_datas.count()
            lis = list(drugs_datas.values())
            for i in range(len(lis)):       # 级联数据
                lis[i]['company_id'] = search_company_name
        else:
            drugs_datas = Herbs.objects.filter(company_id=company)
            default_company_name = Company.objects.get(id=company).name
            data_count += drugs_datas.count()
            lis = list(drugs_datas.values())
            for i in range(len(lis)):       # 级联数据
                lis[i]['company_id'] = default_company_name
    elif type == 'company_table':
        q1 = Q()
        q1.connector = 'OR'
        companyname = request.GET.get('companyname')
        companycode = request.GET.get('companycode')
        creatTimeStart = request.GET.get('creattimestart')
        creatTimeEnd = request.GET.get('creattimeend')
        if companyname:
            q1.children.append(('company_name__contains', companyname))
        if companycode:
            q1.children.append(('company_code', companycode))
        if creatTimeStart and creatTimeEnd:
            q1.children.append(('create_time__range', (creatTimeStart, creatTimeEnd)))
        if q1.children:
            companydatas = Company.objects.filter(q1)
            data_count += companydatas.count()
            lis = list(companydatas.values())
        else:
            company_datas = Company.objects.all()
            data_count += company_datas.count()
            lis = list(company_datas.values())
    elif type == 'order_lists':
        order_q1 = Q()
        order_q2 = Q()
        order_q3 = Q()
        order_q1.connector = 'AND'
        order_q2.connector = 'AND'
        order_q3.connector = 'OR'
        company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        company_search = request.GET.get('company')
        consignee = request.GET.get('consignee')
        order_id = request.GET.get('orderId')
        order_status = request.GET.get('orderStatus')
        prescri_type = request.GET.get('prescriType')
        reg_num = request.GET.get('regNum')
        user_name = request.GET.get('userName')
        zhyf_order_id = request.GET.get('zhyfOrderId')
        start_date = request.GET.get('orderTimeStart')
        end_date = request.GET.get('orderTimeEnd')
        if start_date and end_date:
            order_q1.children.append(('order_time__range', (start_date, end_date)))
        if consignee:
            order_q1.children.append(('consignee', consignee))
        if order_status:
            if order_status == '1':
                order_q1.children.append(('order_status__gte', order_status))
            else:
                order_q1.children.append(('order_status', order_status))
        if company_search:
            order_q1.children.append(('company_id', company_search))
        if prescri_type:
            order_q2.children.append(('prescri_type', prescri_type))
        if order_id:
            order_q1.children.append(('order_id', order_id))
        if user_name:
            order_q2.children.append(('user_name', user_name))
        if reg_num:
            order_q1.children.append(('reg_num', reg_num))
        if zhyf_order_id:
            order_q1.children.append(('zhyf_order_id', zhyf_order_id))
        if order_q1.children and order_q2.children:
            prescription_datas = Prescription.objects.filter(order_q2)
            # print(prescription_datas)
            count = prescription_datas.count()
            # print(count)
            if count:
                for num in range(count):
                    order_id = prescription_datas[num].order_set.all().values('order_id')[0]['order_id']
                    order_q3.children.append(('order_id', order_id))
                order_datas = Order.objects.filter(order_q1 & order_q3)
            else:
                order_datas = prescription_datas
        elif order_q1.children:
            order_datas = Order.objects.filter(order_q1)
        elif order_q2.children:
            prescription_datas = Prescription.objects.filter(order_q2)
            count = prescription_datas.count()
            if count:
                for num in range(count):
                    order_id = prescription_datas[num].order_set.all().values('order_id')[0]['order_id']
                    order_q3.children.append(('order_id', order_id))
                order_datas = Order.objects.filter(order_q3)
            else:
                order_datas = prescription_datas
        else:
            order_datas = Order.objects.filter(company_id=company)
            # print(order_datas)
        data_count += order_datas.count()
        lis = list(order_datas.values())
        for i in range(len(lis)):
            lis[i]['prescri_type'] = order_datas[i].pres_num.prescri_type
            lis[i]['user_name'] = order_datas[i].pres_num.user_name
            lis[i]['company_id'] = Company.objects.get(id=company).name
            lis[i]['addr_str'] = order_datas[i].provinces + ',' + order_datas[i].city + ',' + \
                                 order_datas[i].zone + ',' + order_datas[i].addr_str
    elif type == 'drugs_table':
        pres_num = request.GET.get('prescri_id')
        drugs_datas = PresDetails.objects.filter(prescri_id=pres_num)
        data_count += drugs_datas.count()
        lis = list(drugs_datas.values())
        # for i in range(len(lis)):
        #     lis[i]['unit_sum'] = Decimal(Decimal(drugs_datas[i].dose).quantize(Decimal('0.00')) *
        #                                  Decimal(drugs_datas[i].unit_price).quantize(Decimal('0.00000'))).quantize(
        #         Decimal('0.00'))
        # result = {"code": 0, "msg": "", "count": data_count, "data": lis}
        # return HttpResponse(json.dumps(result, cls=DateEncoder, ensure_ascii=False), content_type="application/json")
    elif type == 'reconciliation_lists':
        order_q1 = Q()
        order_q2 = Q()
        order_q3 = Q()
        order_q1.connector = 'AND'
        order_q2.connector = 'AND'
        order_q3.connector = 'OR'
        company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        company_search = request.GET.get('company')
        is_suffering = request.GET.get('isSuffering')
        start_date = request.GET.get('orderTimeStart')
        end_date = request.GET.get('orderTimeEnd')
        if start_date and end_date:
            order_q1.children.append(('order_time__range', (start_date, end_date)))
        if company_search:
            order_q1.children.append(('company_id', company_search))
        if is_suffering:
            order_q2.children.append(('is_suffering', is_suffering))
        if order_q1.children or order_q2.children:
            if order_q2.children and order_q1.children:
                prescription_datas = Prescription.objects.filter(order_q2)
                count = prescription_datas.count()
                if count:
                    for num in range(count):
                        order_id = prescription_datas[num].order_set.all().values('order_id')[0]['order_id']
                        order_q3.children.append(('order_id', order_id))
                    order_datas = Order.objects.filter(order_q1 & order_q3 & Q(order_status=-1))
                else:
                    order_datas = prescription_datas
            elif order_q1.children:
                order_datas = Order.objects.filter(order_q1 & Q(order_status=-1))
            else:
                prescription_datas = Prescription.objects.filter(order_q2)
                count = prescription_datas.count()
                if count:
                    for num in range(count):
                        order_id = prescription_datas[num].order_set.all().values('order_id')[0]['order_id']
                        order_q3.children.append(('order_id', order_id))
                    order_datas = Order.objects.filter(order_q3 & Q(order_status=-1))
                else:
                    order_datas = prescription_datas
            data_count += order_datas.count()
            lis = list(order_datas.values())
        else:
            order_datas = Order.objects.filter(Q(company_id=company) & Q(order_status=-1))
            data_count += order_datas.count()
            lis = list(order_datas.values())
        for i in range(len(lis)):
            lis[i]['user_name'] = order_datas[i].pres_num.user_name
            lis[i]['tel'] = order_datas[i].pres_num.tel
            lis[i]['amount'] = order_datas[i].pres_num.amount
            lis[i]['per_pack_num'] = order_datas[i].pres_num.per_pack_num
            lis[i]['suffering_num'] = order_datas[i].pres_num.suffering_num
            lis[i]['pres_price_totle'] = order_datas[i].pres_num.pres_price_totle
            lis[i]['pres_sale_price_totle'] = order_datas[i].pres_num.pres_sale_price_totle
            lis[i]['is_suffering'] = order_datas[i].pres_num.is_suffering
    elif type == 'presSalesCount':
        dict_datas = {'company': '', 'count_man': '', 'pres_totle': 0, 'suffer_pres_totle': 0,
                      'not_suffer_pres_totle': 0, 'amount_totle': 0, 'suffer_amount_totle': 0,
                      'not_suffer_amount_totle': 0, 'drugs_price_totle': 0, 'suffer_num_totle': 0,
                      'suffer_price_totle': 0, 'price_totle': 0}
        order_q1 = Q()
        order_q1.connector = 'AND'
        company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        company_search = request.GET.get('company')
        start_date = request.GET.get('orderTimeStart')
        end_date = request.GET.get('orderTimeEnd')
        if company_search:
            order_q1.children.append(('company_id', company_search))
        if start_date and end_date:
            order_q1.children.append(('order_time__range', (start_date, end_date)))
        if order_q1.children:
            order_datas = Order.objects.filter(order_q1 & Q(order_status=-1))
            dict_datas['company'] = Company.objects.get(id=company_search).name
        else:
            order_datas = Order.objects.filter(Q(company_id=company) & Q(order_status=-1))
            dict_datas['company'] = Company.objects.get(id=company).name
        data_count += order_datas.count()
        # print(dict_datas)
        dict_datas['count_man'] = request.session.get('client_user_name')
        dict_datas['pres_totle'] = data_count
        for i in range(data_count):
            prescription = order_datas[i].pres_num
            if prescription.is_suffering == 1:
                dict_datas['suffer_pres_totle'] += 1
                dict_datas['suffer_amount_totle'] += prescription.amount
                dict_datas['suffer_num_totle'] += prescription.suffering_num
                dict_datas['suffer_price_totle'] += prescription.suffering_price
            else:
                dict_datas['not_suffer_pres_totle'] += 1
                dict_datas['not_suffer_amount_totle'] += prescription.amount
            dict_datas['amount_totle'] += prescription.amount
            dict_datas['drugs_price_totle'] += prescription.drug_price
            dict_datas['price_totle'] += order_datas[i].order_price_totle
        # print(dict_datas)
        lis.append(dict_datas)
        # print(lis)
    elif type == 'drugsSalesCount':
        pres_id_list = []
        order_q1 = Q()
        order_q2 = Q()
        order_q1.connector = 'AND'
        order_q2.connector = 'AND'
        company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        company_search = request.GET.get('company')
        drugs_code = request.GET.get('drugsCode')
        drugs_name = request.GET.get('drugsName')
        start_date = request.GET.get('orderTimeStart')
        end_date = request.GET.get('orderTimeEnd')
        if company_search:
            order_q1.children.append(('company_id', company_search))
        if start_date and end_date:
            order_q1.children.append(('order_time__range', (start_date, end_date)))
        if drugs_name:
            order_q2.children.append(('medicines', drugs_name))
        if drugs_code:
            order_q2.children.append(('drugs_num', drugs_code))
        if order_q1.children or order_q2.children:
            pres_datas = Order.objects.filter(order_q1 & Q(order_status=-1)).values('pres_num_id')
            # print(pres_datas)
            for num in range(len(pres_datas)):
                pres_id_list.append(pres_datas[num]['pres_num_id'])
            drugs_datas = PresDetails.objects.filter(prescri_id_id__in=pres_id_list)
            drugs_datas_group = drugs_datas.values('drugs_num', 'medicines', 'unit', 'unit_price').annotate(dose_totle=Sum('sum_dose'))
            if order_q2.children:
                drugs = drugs_datas_group.filter(order_q2)
            else:
                drugs = drugs_datas_group
            data_count += drugs.count()
            lis = list(drugs)
            for i in range(len(lis)):
                lis[i]['company'] = Company.objects.get(id=company_search).name
                lis[i]['price_totle'] = Decimal(float(drugs_datas_group[i]['unit_price']) * drugs_datas_group[i]['dose_totle']).quantize(Decimal("0.00000"))
        else:
            pres_datas = Order.objects.filter(Q(company_id=company) & Q(order_status=-1)).values('pres_num_id')
            # print(pres_datas)
            for num in range(len(pres_datas)):
                pres_id_list.append(pres_datas[num]['pres_num_id'])
            # print(pres_id_list)
            drugs_datas = PresDetails.objects.filter(prescri_id_id__in=pres_id_list)
            # print(drugs_datas.count())
            drugs_datas_group = drugs_datas.values('drugs_num', 'medicines', 'unit', 'unit_price').annotate(
                dose_totle=Sum('sum_dose'))
            # print(drugs_datas_group)
            # print(drugs_datas_group.count())
            data_count += drugs_datas_group.count()
            lis = list(drugs_datas_group)
            # print(lis)
            for i in range(len(lis)):
                lis[i]['company'] = Company.objects.get(id=company).name
                lis[i]['price_totle'] = Decimal(
                    float(drugs_datas_group[i]['unit_price']) * drugs_datas_group[i]['dose_totle']).quantize(
                    Decimal("0.00000"))
    elif type == 'prescription_lists':
        pres_q1 = Q()
        pres_q1.connector = 'AND'
        company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        company_search = request.GET.get('company')
        is_suffering = request.GET.get('isSuffering')
        start_date = request.GET.get('orderTimeStart')
        end_date = request.GET.get('orderTimeEnd')
        if start_date and end_date:
            pres_q1.children.append(('create_time__range', (start_date, end_date)))
        if company_search:
            pres_q1.children.append(('company_id', company_search))
        if is_suffering:
            pres_q1.children.append(('is_suffering', is_suffering))
        if pres_q1.children:
            prescription_datas = Prescription.objects.filter(pres_q1)
            data_count += prescription_datas.count()
        else:
            prescription_datas = Prescription.objects.filter(company_id=company)
            data_count += prescription_datas.count()
        lis = list(prescription_datas.values())
    page_index = request.GET.get('page')  # 前台传的值
    page_size = request.GET.get('limit')  # 前台传的值
    paginator = Paginator(lis, page_size)  # 导入分页模块分页操作，不写前端只展示一页数据，
    contacts = paginator.page(page_index)  # 导入分页模块分页操作，不写前端只展示一页数据，
    res = []
    for contact in contacts:
        res.append(contact)
    result = {"code": 0, "msg": "", "count": data_count, "data": res}
    # print(result)
    return HttpResponse(json.dumps(result, cls=DateEncoder, ensure_ascii=False), content_type="application/json")


@csrf_exempt
def role_manage(request, type):
    if type == 'roleAdd':
        context = {}
        if request.method == 'POST':
            role = Role()
            # print(request.POST.get('rolename'))
            role.role_name = request.POST.get('rolename')
            try:
                role.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        return render(request, 'hospital/systemManage/user/role_add.html')
    if type == 'roleEdit':
        context = {}
        if request.method == 'POST':
            role = Role.objects.get(id=request.POST.get('roleid'))
            role.role_name = request.POST.get('rolename')
            try:
                role.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        return render(request, 'hospital/systemManage/user/role_add.html')
    if type == 'roleDelete':
        context = {}
        try:
            Role.objects.get(id=request.POST.get('delData')).delete()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'menuData':
        menu_datalist = list(Menu.objects.all().values())
        # print(menu_datalist)
        # print(len(menu_datalist))
        menu_data = []
        parent_id = []
        for num in range(len(menu_datalist)):
            # print(menu_datalist[num]['parent_id'])
            if menu_datalist[num]['parent_id'] == None:
                del menu_datalist[num]['icon']
                del menu_datalist[num]['parent_id']
                menu_datalist[num]['children'] = []
                menu_data.append(menu_datalist[num])
                parent_id.append(menu_datalist[num]['id'])
                # print(menu_data)
                # print(parent_id)
            else:
                for n in range(len(parent_id)):
                    if menu_datalist[num]['parent_id'] == parent_id[n]:
                        del menu_datalist[num]['icon']
                        del menu_datalist[num]['parent_id']
                        menu_data[n]['children'].append(menu_datalist[num])
                        break
                    else:
                        continue
        context = {'menuData': menu_data}
        role = Role.objects.get(id=request.GET.get('roleId'))
        permissions = list(role.permissions.all().values())
        # print(permissions)
        menu_ids = []
        if permissions:
            for num in range(len(permissions)):
                menu_id = Menu.objects.get(title=permissions[num]['title']).id
                menu_ids.append(menu_id)
        context['checkedId'] = menu_ids
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'authorize':
        context = {}
        if request.method == 'POST':
            role = Role.objects.get(id=request.POST.get('roleId'))
            role.permissions.clear()
            auth_data = json.loads(request.POST.get('data'))
            for num in range(len(auth_data)):
                for n in range(len(auth_data[num]['children'])):
                    title = auth_data[num]['children'][n]['title']
                    auth = Permission.objects.filter(title=title).first()
                    if auth:
                        role.permissions.add(auth)
                        context['status'] = 'success'
                    else:
                        au = Permission()
                        url = ''
                        per_id = ''
                        if title == '菜单管理':
                            url += "/hospital_client/menuManage/home/"
                            per_id += 'menu_manage'
                        elif title == '用户管理':
                            url += "/hospital_client/userManage/home/"
                            per_id += 'user_manage'
                        elif title == '角色管理':
                            url += "/hospital_client/roleManage/home/"
                            per_id += 'role_manage'
                        elif title == '机构管理':
                            url += "/hospital_client/companyManage/home"
                            per_id += 'company_manage'
                        elif title == '药品管理':
                            url += "/hospital_client/drugsManage/home"
                            per_id += 'drugs_manage'
                        elif title == '添加药品':
                            url += "/hospital_client/addDrugs"
                            per_id += 'add_drugs'
                        elif title == '药材批量导入':
                            url += "/hospital_client/batchImportDrugs"
                            per_id += 'batch_import_drugs'
                        elif title == '处方笺':
                            url += "/hospital_client/prescriptionMake/firstStep"
                            per_id += 'prescription_make'
                        elif title == '订单列表查询':
                            url += "/hospital_client/orderListQuery/home"
                            per_id += 'order_lists_query'
                        elif title == '处方查询':
                            url += "/hospital_client/prescriptionQuery"
                            per_id += 'prescription_query'
                        elif title == '医院对账处方清单':
                            url += "/hospital_client/statementsManage/reconciliation"
                            per_id += 'reconciliation'
                        elif title == '处方销售统计报表':
                            url += "/hospital_client/statementsManage/presSalesCount"
                            per_id += 'pres_sales_count'
                        elif title == '药材销售统计报表':
                            url += "/hospital_client/statementsManage/drugsSalesCount"
                            per_id += 'drugs_sales_count'
                        au.title = title
                        au.url = url
                        au.per_id = per_id
                        au.menu = Menu.objects.get(id=auth_data[num]['id'])
                        try:
                            au.save()
                            role.permissions.add(au)
                            context['status'] = 'success'
                        except Exception as e:
                            context['status'] = 'fail'
                            context['message'] = str(e)
                            logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        return render(request, 'hospital/systemManage/user/role_authorize.html')
    if type == 'home':
        return render(request, 'hospital/systemManage/user/role_manage.html')


@csrf_exempt
def user_manage(request, type):
    if type == 'userAdd':
        context = {}
        if request.method == 'POST':
            user = ClientUser()
            user.username = request.POST.get('username')
            user.password = request.POST.get('password')
            user.isnot_showprice = request.POST.get('priceset')
            user.remark = request.POST.get('remark')
            user.company_id_id = request.POST.get('company')
            role = Role.objects.get(id=request.POST.get('role'))
            try:
                user.save()
                user.role.add(role)
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        return render(request, 'hospital/systemManage/user/user_add.html')
    if type == 'userEdit':
        context = {}
        if request.method == 'POST':
            user = ClientUser.objects.get(id=request.POST.get('userId'))
            user.username = request.POST.get('username')
            user.password = request.POST.get('password')
            user.isnot_showprice = request.POST.get('priceset')
            user.remark = request.POST.get('remark')
            user.company_id_id = request.POST.get('company')
            role = Role.objects.get(id=request.POST.get('role'))
            try:
                user.save()
                user.role.add(role)
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        user = ClientUser.objects.get(id=request.GET.get('userId'))
        # print(locals())
        return render(request, 'hospital/systemManage/user/user_add.html', locals())
    if type == 'userDelete':
        context = {}
        # print(request.POST)
        dele_datas = string_to_list(request.POST.get('delData'))
        # print(dele_datas)
        for data in dele_datas:
            try:
                ClientUser.objects.get(username=data).delete()
                context['status'] = 'success'
                context['message'] = '成功删除%s条数据' % len(dele_datas)
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'updateStatus':
        context = {}
        user = ClientUser.objects.get(id=request.POST.get('userid'))
        status = request.POST.get('status')
        if int(status) > 0:
            user.is_disabled = 0
        else:
            user.is_disabled = 1
        try:
            user.save()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'home':
        return render(request, 'hospital/systemManage/user/user_manage.html')


def get_role(request):
    roles = Role.objects.all()
    json_roles = serializers.serialize('json', roles)
    return HttpResponse(json_roles)


def get_company(request):
    company_id = request.GET.get('companyId')
    if company_id:
        company = Company.objects.filter(id=company_id)
        json_company = serializers.serialize('json', company)
        return HttpResponse(json_company)
    else:
        companies = Company.objects.all()
        json_companies = serializers.serialize('json', companies)
        return HttpResponse(json_companies)


@csrf_exempt
def company_manage(request, type):
    context = {}
    if type == 'add':
        if request.method == 'POST':
            company = Company()
            company.name = request.POST.get('companyName')
            company.company_password = request.POST.get('companyPass')
            company.company_code = request.POST.get('companyCode')
            company.tel = request.POST.get('tel')
            company.dj_tel = request.POST.get('dj_tel')
            company.province = request.POST.get('comProvince')
            company.city = request.POST.get('comCity')
            company.zone = request.POST.get('comZone')
            company.address = request.POST.get('comAddress')
            company.introduction = request.POST.get('companyDescription')
            company.isnot_showprice = request.POST.get('priceSet')
            if request.POST.get('nitPrice'):
                company.unitprice = request.POST.get('nitPrice')
            if request.POST.get('packDose'):
                company.per_pack_dose = request.POST.get('packDose')
            if request.POST.get('sendTimeToday'):
                company.sendgoodtime_today = request.POST.get('sendTimeToday')
            if request.POST.get('sendTimeTomorrow'):
                company.sendgoodtime_tomorrow = request.POST.get('sendTimeTomorrow')
            # current_user = request.session['client_user_name']
            # company.createman = current_user
            try:
                company.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        return render(request, 'hospital/systemManage/company/add_company.html')
    if type == 'updateStatus':
        status = request.POST.get('status')
        company = Company.objects.get(id=request.POST.get('companyid'))
        if int(status) > 0:
            company.is_disabled = 0
        else:
            company.is_disabled = 1
        try:
            company.save()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'edit':
        if request.method == 'POST':
            company = Company.objects.get(id=request.POST.get('companyId'))
            company.name = request.POST.get('companyName')
            company.company_password = request.POST.get('companyPass')
            company.company_code = request.POST.get('companyCode')
            company.tel = request.POST.get('tel')
            company.dj_tel = request.POST.get('dj_tel')
            company.province = request.POST.get('comProvince')
            company.city = request.POST.get('comCity')
            company.zone = request.POST.get('comZone')
            company.address = request.POST.get('comAddress')
            company.introduction = request.POST.get('companyDescription')
            company.isnot_showprice = request.POST.get('priceSet')
            if request.POST.get('nitPrice'):
                company.unitprice = request.POST.get('nitPrice')
            if request.POST.get('packDose'):
                company.per_pack_dose = request.POST.get('packDose')
            if request.POST.get('sendTimeToday'):
                company.sendgoodtime_today = request.POST.get('sendTimeToday')
            if request.POST.get('sendTimeTomorrow'):
                company.sendgoodtime_tomorrow = request.POST.get('sendTimeTomorrow')
            try:
                company.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        company_id = request.GET.get('companyid')
        company = Company.objects.get(id=company_id)
        return render(request, 'hospital/systemManage/company/edit_company.html', locals())
    if type == 'home':
        return render(request, 'hospital/systemManage/company/company_manage.html')


@csrf_exempt
def drugs_manage(request, type):
    if type == 'editDrugs':
        context = {}
        drugs_id = request.GET.get('drugsId')
        modify_field = request.GET.get('modified')
        new_value = request.GET.get('newValue')
        drugs = Herbs.objects.get(id=drugs_id)
        setattr(drugs, modify_field, new_value)
        drugs.update_man = request.session.get('client_user_name')
        if modify_field in ('sale_price', 'price'):
            drugs.isnot_handedit = 1
        try:
            drugs.save()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'updateStatus':
        context = {}
        status = request.GET.get('status')
        # print(status)
        if status:
            drugs = Herbs.objects.get(id=request.GET.get('drugsId'))
            if int(status) > 0:
                drugs.status = 0
            else:
                drugs.status = 1
            try:
                drugs.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'home':
        user_login = request.session.get('client_user_name')
        company_belong = ClientUser.objects.get(username=user_login).company_id
        # print(locals())
        return render(request, 'hospital/dataManage/drugsManage/drugs_manage.html', locals())


@csrf_exempt
def add_drugs(request):
    context = {}
    if request.method == 'POST':
        drugs = Herbs()
        drugs.drugs_code = request.POST.get('drugsCode')
        drugs.drugs_name = request.POST.get('drugsName')
        drugs.unit = request.POST.get('unit')
        drugs.short_code = request.POST.get('shortCode')
        drugs.price = Decimal(request.POST.get('price')).quantize(Decimal('0.000'))
        drugs.sale_price = Decimal(request.POST.get('salePrice')).quantize(Decimal('0.000'))
        drugs.company_id = request.POST.get('company')
        drugs.drugs_type = request.POST.get('drugsType')
        if request.POST.get('drugsStatus'):
            drugs.status = request.POST.get('drugsStatus')
        if request.POST.get('alias1'):
            drugs.alias1 = request.POST.get('alias1')
        if request.POST.get('alias2'):
            drugs.alias2 = request.POST.get('alias2')
        if request.POST.get('alias3'):
            drugs.alias3 = request.POST.get('alias3')
        if request.POST.get('alias4'):
            drugs.alias4 = request.POST.get('alias4')
        if request.POST.get('alias5'):
            drugs.alias5 = request.POST.get('alias5')
        if request.POST.get('alias6'):
            drugs.alias6 = request.POST.get('alias6')
        if request.POST.get('alias7'):
            drugs.alias7 = request.POST.get('alias7')
        if request.POST.get('alias8'):
            drugs.alias8 = request.POST.get('alias8')
        if request.POST.get('alias9'):
            drugs.alias9 = request.POST.get('alias9')
        if request.POST.get('alias10'):
            drugs.alias10 = request.POST.get('alias10')
        try:
            drugs.save()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    return render(request, 'hospital/dataManage/addDrugs/add_drugs.html')


@csrf_exempt
def batch_import_drugs(request):
    context = {}
    if request.method == 'POST':
        file = request.FILES['file']
        file_name = '%s/%s' % (settings.MEDIA_ROOT, file.name)
        # print(file_name)
        try:
            with open(file_name, 'wb') as f:
                for f_file in file.chunks():
                    f.write(f_file)
                    context['status'] = 'success'
                    df = pd.read_excel(file_name)
                    # print(df)
                    drugs = []
                    count_control = 0
                    for num in range(len(df)):
                        # print(type(df.loc[num]['药品编码']))
                        # print(df.loc[num]['药品编码'])
                        # print(str(df.loc[num]['药品编码']))
                        drug = Herbs(drugs_code=df.loc[num]['药品编码'], drugs_name=df.loc[num]['药品名称'],
                                     short_code=df.loc[num]['简码'], price=df.loc[num]['结算价'], unit=df.loc[num]['单位'],
                                     sale_price=df.loc[num['销售价格']])
                        logger.info(drug)
                        if not pd.isna(df.loc[num]['库存']):
                            drug.stock = df.loc[num]['库存']
                        if df.loc[num]['状态'] != '否' or df.loc[num]['状态'] != '已停用':
                            drug.status = 1
                        else:
                            drug.status = 0
                        if not pd.isna(df.loc[num]['药品规格']):
                            drug.goods_norms = df.loc[num]['药品规格']
                        if not pd.isna(df.loc[num]['药品产地']):
                            drug.goods_orgin = df.loc[num]['药品产地']
                        if df.loc[num]['类型'] == '中药':
                            drug.drugs_type = 0
                        else:
                            drug.drugs_type = 1
                        if not pd.isna(df.loc[num]['别名1']):
                            drug.alias1 = df.loc[num]['别名1']
                        if not pd.isna(df.loc[num]['别名2']):
                            drug.alias2 = df.loc[num]['别名2']
                        if not pd.isna(df.loc[num]['别名3']):
                            drug.alias3 = df.loc[num]['别名3']
                        if not pd.isna(df.loc[num]['别名4']):
                            drug.alias4 = df.loc[num]['别名4']
                        if not pd.isna(df.loc[num]['别名5']):
                            drug.alias5 = df.loc[num]['别名5']
                        if not pd.isna(df.loc[num]['别名6']):
                            drug.alias6 = df.loc[num]['别名6']
                        if not pd.isna(df.loc[num]['别名7']):
                            drug.alias7 = df.loc[num]['别名7']
                        if not pd.isna(df.loc[num]['别名8']):
                            drug.alias8 = df.loc[num]['别名8']
                        if not pd.isna(df.loc[num]['别名9']):
                            drug.alias9 = df.loc[num]['别名9']
                        if not pd.isna(df.loc[num]['别名10']):
                            drug.alias10 = df.loc[num]['别名10']
                        count_control += 1
                        drugs.append(drug)
                        # print(drug)
                        # print(drugs)
                        if count_control >= 100:  # 每100条数据执行一次插入
                            Herbs.objects.bulk_create(drugs)
                            count_control = 0  # 计数归0
                            drugs.clear()  # 清空列表
                    Herbs.objects.bulk_create(drugs)
                    context['message'] = '导入成功'
        except Exception as e:
            # print(e)
            context['status'] = 'false'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    return render(request, 'hospital/dataManage/BatchImportGoods.html')


@csrf_exempt
def prescription_make(request, type):
    if type == 'firstStep':
        if request.method == 'POST':
            context = {}
            pres_dict = query_dict2python_dict(dict(request.POST))
            pres_base_info = Prescription(prescri_id=str(time.time()).split('.')[0],
                                          user_name=pres_dict['user_name'], age=pres_dict['age'],
                                          treat_card_id=pres_dict['treat_card'],
                                          tel=pres_dict['tel'], gender=pres_dict['gender'],
                                          is_pregnant=pres_dict.get('is_pregnant', 2),
                                          is_hos=pres_dict['is_hos'], is_suffering=pres_dict['is_suffering'],
                                          amount=pres_dict['amount'], suffering_num=pres_dict['suffering_num'],
                                          ji_fried=pres_dict.get('ji_fried', 1), prescri_type=pres_dict['prescri_type'],
                                          is_within=pres_dict['is_within'],
                                          special_instru=pres_dict.get('special_instru', ''),
                                          bed_num=pres_dict.get('bed_num', ''),
                                          hos_depart=pres_dict.get('hos_depart', ''),
                                          hospital_num=pres_dict.get('hospital_num', ''),
                                          disease_code=pres_dict.get('disease_code', ''),
                                          doctor=pres_dict.get('doctor', ''),
                                          paste_desc_file=pres_dict.get('paste_desc_file', ''),
                                          prescript_remark=pres_dict.get('prescript_remark', ''),
                                          per_pack_num=pres_dict['per_pack_num'], per_pack_dose=pres_dict['per_pack_dose'],
                                          sea_doctor_time=pres_dict['seaDoctotTime'],
                                          medication_methods=pres_dict.get('medication_methods', ''),
                                          medication_instruction=pres_dict.get('medication_instruction', ''),
                                          )
            company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
            pres_base_info.company_id = company
            if pres_dict['is_suffering'] == '1':
                unit_suffer_price = Company.objects.get(id=company).unitprice
                pres_base_info.suffering_price = unit_suffer_price * int(pres_dict['suffering_num'])
            try:
                pres_base_info.save()
                context['status'] = 'success'
                context['pres_base_info'] = pres_base_info.obj2dict()
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        now_time = str(datetime.datetime.now())
        sea_doctor_time = now_time.split('.')[0]
        treat_card_id = now_time.split('.')[1]
        return render(request, 'hospital/orderManage/prescription_first.html', locals())
    if type == 'secondStep':
        if request.method == 'POST':
            prescription = Prescription.objects.get(prescri_id=request.POST.get('presId'))
            context = {}
            q1 = Q()
            q1.connector = 'AND'
            q1.children.append(('prescri_id', request.POST.get('presId')))
            q1.children.append(('drugs_num', request.POST.get('drugs_num')))
            is_exist = PresDetails.objects.filter(q1)
            if is_exist:
                context['status'] = 'fail'
                context['message'] = '重复添加药品!'
                return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
            pres_detail_info = PresDetails()
            pres_detail_info.prescri_id = prescription
            pres_detail_info.drugs_num = request.POST.get('drugs_num')
            pres_detail_info.medicines = request.POST.get('medicines')
            pres_detail_info.dose = request.POST.get('dose')
            pres_detail_info.sum_dose = int(request.POST.get('dose')) * prescription.amount
            pres_detail_info.unit = request.POST.get('unit')
            pres_detail_info.unit_price = request.POST.get('unit_price')
            pres_detail_info.unit_price_totle = request.POST.get('unit_price_totle')
            pres_detail_info.sale_price = request.POST.get('sale_price')
            pres_detail_info.sale_price_totle = request.POST.get('sale_price_totle')
            if request.POST.get('m_usage'):
                pres_detail_info.m_usage = request.POST.get('m_usage')
            if request.POST.get('remark'):
                pres_detail_info.remark = request.POST.get('remark')
            pres_detail_info.update_man = request.session.get('client_user_name')
            try:
                pres_detail_info.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        pres_id = request.GET.get('prescri_id')
        order_id = request.GET.get('order_id')
        # print(pres_id)
        # print(order_id)
        pres_info = Prescription.objects.get(prescri_id=pres_id)
        return render(request, 'hospital/orderManage/prescription_second.html', locals())
    if type == 'addPrescriptionDrugs':
        pres_id = request.GET.get('prescri_id')
        # print(locals())
        return render(request, 'hospital/orderManage/pres_drug_add.html', locals())
    if type == 'editDoseRemark':
        context = {}
        drugs_id = request.GET.get('drugsId')
        modify_field = request.GET.get('modified')
        new_value = request.GET.get('newValue')
        prescription = Prescription.objects.get(prescri_id=request.GET.get('pres_num'))
        drugs = PresDetails.objects.get(id=drugs_id)
        if modify_field == 'dose':
            setattr(drugs, modify_field, new_value)
            drugs.unit_price_totle = int(new_value) * drugs.unit_price
            drugs.sale_price_totle = int(new_value) * drugs.sale_price
            drugs.sum_dose = int(new_value) * prescription.amount
        else:
            setattr(drugs, modify_field, new_value)
        drugs.update_man = request.session.get('client_user_name')
        try:
            drugs.save()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'drugDelete':
        context = {}
        # print(request.POST)
        dele_datas = string_to_list(request.POST.get('delData'))
        # print(dele_datas)
        for data in dele_datas:
            try:
                PresDetails.objects.get(id=data).delete()
                context['status'] = 'success'
                context['message'] = '成功删除%s条数据' % len(dele_datas)
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")


def get_herbs(request):
    company_id = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
    short_code = request.GET.get('shortCode')
    # print(short_code)
    q = Q()
    q.connector = 'AND'
    if short_code:
        q.children.append(('short_code__contains', short_code))
    if company_id:
        q.children.append(('company_id', company_id))
    herbs = Herbs.objects.filter(q)
    # print(herbs)
    json_herbs = serializers.serialize('json', herbs)
    return HttpResponse(json_herbs)


@csrf_exempt
def make_order(request, type):
    if type == 'home':
        now_time = str(datetime.datetime.now())
        order_id = now_time.split('.')[1]
        reg_num = now_time.split(' ')[0].replace('-', '') + str(time.time()).split('.')[1]
        prescri_id = request.GET.get('prescri_id')
        prescription = Prescription.objects.get(prescri_id=prescri_id)
        pres_details = PresDetails.objects.filter(prescri_id=prescri_id)
        if pres_details:
            one_mount_drug_price = pres_details.aggregate(Sum('unit_price_totle'))
            one_mount_drug_sale_price = pres_details.aggregate(Sum('sale_price_totle'))
            pre_drug_price = one_mount_drug_price['unit_price_totle__sum'] * prescription.amount
            pre_drug_sale_price = one_mount_drug_sale_price['sale_price_totle__sum'] * prescription.amount
        else:
            pre_drug_price = 0
            pre_drug_sale_price = 0
        prescription.drug_price = pre_drug_price
        prescription.drug_sale_price = pre_drug_sale_price
        prescription.pres_price_totle = pre_drug_price + prescription.suffering_price
        prescription.pres_sale_price_totle = pre_drug_sale_price + prescription.suffering_price
        prescription.is_order += 1
        prescription.save()
        company_name = Company.objects.get(id=prescription.company_id).name
        if request.GET.get('order_id'):
            order = Order.objects.get(order_id=request.GET.get('order_id'))
        else:
            order = Order()
            order.order_id = order_id
            order.order_time = now_time.split('.')[0]
            order.reg_num = reg_num
            order.treat_card = prescription.treat_card_id
            order.pres_num_id = prescri_id
            order.creat_man = request.session.get('client_user_name')
            order.company_id = prescription.company_id
        order.order_price_totle = prescription.pres_price_totle
        order.order_sale_price_totle = prescription.pres_sale_price_totle
        order.save()
        send_goods_addr = order.provinces + ',' + order.city + ',' + order.zone + ',' + order.addr_str
        return render(request, 'hospital/orderManage/make_order.html', locals())
    if type == 'modifyPrescription':
        context = {}
        pres = Prescription.objects.get(prescri_id=request.POST.get('pres_id'))
        new_is_suffering = int(request.POST.get('is_suffering'))
        new_amount = int(request.POST.get('amount'))
        new_per_pack_num = int(request.POST.get('per_pack_num'))
        new_pres_remark = request.POST.get('prescript_remark')
        company = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        unit_suffer_price = Company.objects.get(id=company).unitprice
        new_suffering_num = new_amount * new_per_pack_num
        if new_amount and new_amount != int(pres.amount):
            cursor = connection.cursor()
            cursor.execute("update tb_prescriptions_details set sum_dose = dose * %s where prescri_id_id = %s", [
                new_amount, request.POST.get('pres_id')])
        if new_is_suffering == 1 and pres.is_suffering == 0:
            pres.per_pack_dose = 200
        if new_is_suffering == 0 and pres.is_suffering == 1:
            pres.per_pack_dose = 0
        pres.is_suffering = new_is_suffering
        pres.amount = new_amount
        pres.per_pack_num = new_per_pack_num
        pres.suffering_num = new_suffering_num
        pres.suffering_price = new_suffering_num * unit_suffer_price
        pres.prescript_remark = request.POST.get('prescript_remark')
        try:
            pres.save()
            context['status'] = 'success'
        except Exception as e:
            context['status'] = 'fail'
            context['message'] = str(e)
            logger.error(context)
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'addOrderAddress':
        if request.method == 'POST':
            context = {}
            order = Order.objects.get(order_id=request.POST.get('order_id'))
            order.addr_str = request.POST.get('addr_str')
            order.provinces = request.POST.get('comProvince')
            order.city = request.POST.get('comCity')
            order.zone = request.POST.get('comZone')
            order.consignee = request.POST.get('consignee')
            order.con_tel = request.POST.get('con_tel')
            order.is_hos_addr = request.POST.get('is_hos_addr')
            if request.POST.get('send_goods_time'):
                order.send_goods_time = request.POST.get('send_goods_time')
            order.update_man = request.session.get('client_user_name')
            try:
                order.save()
                context['status'] = 'success'
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        if request.GET.get('order_id'):
            order = Order.objects.get(order_id=request.GET.get('order_id'))
        company_id = ClientUser.objects.get(username=request.session.get('client_user_name')).company_id.id
        return render(request, 'hospital/orderManage/add_address.html', locals())


def save_order(request):
    context = {}
    order_id = request.GET.get('orderId')
    prescription_id = request.GET.get('presId')
    # print(order_id)
    # print(prescription_id)
    order = Order.objects.get(order_id=order_id)
    prescription = Prescription.objects.get(prescri_id=prescription_id)
    company = Company.objects.get(id=prescription.company_id)
    pres_details = PresDetails.objects.filter(prescri_id=prescription_id)
    if pres_details and order.addr_str:
        result = upload_prescription(order, prescription, pres_details, company)
        logger.info(result)
        if result.get('orderId'):
            context['status'] = 'success'
            order.zhyf_order_id = result.get('orderId')
            order.order_status = -1
            prescription.order_status = -1
            order.save()
            prescription.save()
        elif result.get('specialCode') == '22':
            context['status'] = 'fail'
            context['message'] = '请勿重复提交订单！'
        else:
            context['status'] = 'fail'
            context['message'] = result.get('message')
            order.order_status += 1
            order.save()
    elif pres_details:
        context['status'] = 'fail'
        context['message'] = '请录入收货信息！'
    elif order.addr_str:
        context['status'] = 'fail'
        context['message'] = '该处方无药品！'
    else:
        context['status'] = 'fail'
        context['message'] = '请检查订单信息(处方药品｜收货信息)完整性！'
    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")


def order_list_query(request, type):
    if type == 'home':
        user_login = request.session.get('client_user_name')
        company_belong = ClientUser.objects.get(username=user_login).company_id
        return render(request, 'hospital/orderManage/order_lists.html', locals())


def statements_manage(request, type):
    if type == 'reconciliation':
        user_login = request.session.get('client_user_name')
        company_belong = ClientUser.objects.get(username=user_login).company_id
        return render(request, 'hospital/statementsManage/reconciliation.html', locals())
    if type == 'presSalesCount':
        user_login = request.session.get('client_user_name')
        company_belong = ClientUser.objects.get(username=user_login).company_id
        return render(request, 'hospital/statementsManage/pres_sales_count.html', locals())
    if type == 'drugsSalesCount':
        user_login = request.session.get('client_user_name')
        company_belong = ClientUser.objects.get(username=user_login).company_id
        return render(request, 'hospital/statementsManage/drugs_sales_count.html', locals())


def prescription_query(request):
    user_login = request.session.get('client_user_name')
    company_belong = ClientUser.objects.get(username=user_login).company_id
    return render(request, 'hospital/orderManage/prescriptions_lists.html', locals())


def re_order(request):
    context = {}
    pres_num = request.GET.get('prescri_id')
    # print(pres_num)
    old_prescription = Prescription.objects.get(prescri_id=pres_num)
    old_pres_detail = PresDetails.objects.filter(prescri_id=pres_num)
    logger.info(old_prescription.obj2dict())
    new_prescription = Prescription(prescri_id=str(time.time()).split('.')[0],
                                    user_name=old_prescription.user_name, age=old_prescription.age,
                                    treat_card_id=old_prescription.treat_card_id,
                                    tel=old_prescription.tel, gender=old_prescription.gender,
                                    is_pregnant=old_prescription.is_pregnant,
                                    is_hos=old_prescription.is_hos, is_suffering=old_prescription.is_suffering,
                                    amount=old_prescription.amount, suffering_num=old_prescription.suffering_num,
                                    ji_fried=old_prescription.ji_fried,
                                    prescri_type=old_prescription.prescri_type,
                                    is_within=old_prescription.is_within,
                                    special_instru=old_prescription.special_instru,
                                    bed_num=old_prescription.bed_num,
                                    hos_depart=old_prescription.hos_depart,
                                    hospital_num=old_prescription.hospital_num,
                                    disease_code=old_prescription.disease_code,
                                    doctor=old_prescription.doctor,
                                    paste_desc_file=old_prescription.paste_desc_file,
                                    prescript_remark=old_prescription.prescript_remark,
                                    per_pack_num=old_prescription.per_pack_num,
                                    per_pack_dose=old_prescription.per_pack_dose,
                                    sea_doctor_time=str(datetime.datetime.now()).split('.')[0],
                                    medication_methods=old_prescription.medication_methods,
                                    medication_instruction=old_prescription.medication_instruction,
                                    company_id=old_prescription.company_id,
                                    suffering_price=old_prescription.suffering_price
                                    )
    try:
        new_prescription.save()
        context['status'] = 'success'
    except Exception as e:
        context['status'] = 'fail'
        context['message'] = str(e)
        logger.error(context)
    if context['status'] == 'success':
        for num in range(old_pres_detail.count()):
            new_pres_detail = PresDetails()
            new_pres_detail.prescri_id = Prescription.objects.get(prescri_id=new_prescription.prescri_id)
            new_pres_detail.drugs_num = old_pres_detail[num].drugs_num
            new_pres_detail.medicines = old_pres_detail[num].medicines
            new_pres_detail.dose = old_pres_detail[num].dose
            new_pres_detail.sum_dose = old_pres_detail[num].sum_dose
            new_pres_detail.unit = old_pres_detail[num].unit
            new_pres_detail.unit_price = old_pres_detail[num].unit_price
            new_pres_detail.unit_price_totle = old_pres_detail[num].unit_price_totle
            new_pres_detail.sale_price = old_pres_detail[num].sale_price
            new_pres_detail.sale_price_totle = old_pres_detail[num].sale_price_totle
            new_pres_detail.m_usage = old_pres_detail[num].m_usage
            new_pres_detail.remark = old_pres_detail[num].remark
            new_pres_detail.update_man = old_pres_detail[num].update_man
            try:
                new_pres_detail.save()
                context['status'] = 'success'
                context['new_pres_id'] = new_prescription.prescri_id
            except Exception as e:
                context['status'] = 'fail'
                context['message'] = str(e)
                logger.error(context)
    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")


def print_prescription(request, type):
    if type == 'home':
        pres_num = request.GET.get('presId')
        order_id = request.GET.get('orderId')
        prescription = Prescription.objects.get(prescri_id=pres_num)
        order = Order.objects.get(order_id=order_id)
        company = Company.objects.get(id=prescription.company_id).name
        address = order.provinces + ',' + order.city + ',' + order.zone + ',' + order.addr_str
        oper_user = request.session.get('client_user_name')
        return render(request, 'hospital/orderManage/prescription_model.html', locals())
    if type == 'drugs':
        data_count = 0
        pres_num = request.GET.get('prescriId')
        drugs_datas = PresDetails.objects.filter(prescri_id=pres_num)
        json_drugs = serializers.serialize('json', drugs_datas)
        return HttpResponse(json_drugs)


def cancel_order(request):
    context = {}
    order_id = request.GET.get('orderId')
    prescription_id = request.GET.get('presId')
    order = Order.objects.get(order_id=order_id)
    prescription = Prescription.objects.get(prescri_id=prescription_id)
    zhyf_order_id = order.zhyf_order_id
    current_user = request.session.get('client_user_name')
    company = Company.objects.get(id=ClientUser.objects.get(username=current_user).company_id_id)
    reason = '用户取消订单！'
    # print(order_id)
    # print(prescription_id)
    result = cancel(current_user, reason, zhyf_order_id, company)
    if result.get('status'):
        if result.get('status') == 'success':
            context['status'] = 'success'
            order.order_status = 99
            prescription.order_status = 99
            order.save()
            prescription.save()
        else:
            context['status'] = 'fail'
            context['message'] = result.get('message')
    else:
        context['status'] = 'fail'
        context['message'] = result.get('message')
    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")