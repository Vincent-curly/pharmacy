# coding:utf-8
"""
  Time : 2021/2/2 下午5:14
  Author : vincent
  FileName: urls
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2021/2/2 下午5:14
"""
from django.conf.urls import url

from hospital_client import views

urlpatterns = [
    url(r'^login/', views.login, name='login'),
    url(r'^index/', views.index, name='index'),
    url(r'^logout/', views.logout, name='logout'),
    url(r'^home/', views.home, name='home'),
    url(r'^role/', views.get_role, name='role'),
    url(r'^company/', views.get_company, name='company'),
    url(r'^herbs/', views.get_herbs, name='herbs'),
    url(r'^updatePass/', views.update_pass, name='updatePass'),
    url(r'^changeVerifyCode/', views.change_verify_code, name='changeVerifyCode'),
    url(r'^tableData/(?P<type>\w+)/', views.table_data, name='tableData'),
    url(r'^menuManage/(?P<type>\w+)/', views.menu_manage, name='menuManage'),
    url(r'^roleManage/(?P<type>\w+)/', views.role_manage, name='roleManage'),
    url(r'^userManage/(?P<type>\w+)/', views.user_manage, name='userManage'),
    url(r'^companyManage/(?P<type>\w+)', views.company_manage, name='companyManage'),
    url(r'^drugsManage/(?P<type>\w+)/', views.drugs_manage, name='drugsManage'),
    url(r'^addDrugs/', views.add_drugs, name='addDrugs'),
    url(r'^batchImportDrugs/', views.batch_import_drugs, name='batchImportDrugs'),
    url(r'^prescriptionMake/(?P<type>\w+)/', views.prescription_make, name='prescriptionMake'),
    url(r'^makeOrder/(?P<type>\w+)/', views.make_order, name='makeOrder'),
    url(r'^saveOrder/', views.save_order, name='saveOrder'),
    url(r'^reOrder/', views.re_order, name='reOrder'),
    url(r'^cancelOrder/', views.cancel_order, name='cancelOrder'),
    url(r'^orderListQuery/(?P<type>\w+)/', views.order_list_query, name='orderListQuery'),
    url(r'^prescriptionQuery/', views.prescription_query, name='prescriptionQuery'),
    url(r'^statementsManage/(?P<type>\w+)/', views.statements_manage, name='statementsManage'),
    url(r'^printPrescription/(?P<type>\w+)/', views.print_prescription, name='printPrescription')
]
