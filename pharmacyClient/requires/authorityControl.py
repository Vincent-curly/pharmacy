# coding:utf-8
"""
  Time : 2021/2/6 上午3:12
  Author : vincent
  FileName: authorityControl
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2021/2/6 上午3:12
"""
from django.utils.safestring import mark_safe


def get_menu_html(menu_data, permission_data):
    """显示：菜单 + [子菜单] + 权限(url)"""
    menu_str = """
    <a href="javascript:;"><span class="{menu_icon}"></span>&nbsp;&nbsp;{menu_title}</a>
    """

    permission_str = """
        <dd><a data-url="{per_url}" data-id="{per_id}" data-title="{per_title}" class="nav-active"
            href="javascript:;" data-type="tabAdd">&nbsp;&nbsp;&nbsp;<span class="iconfont icon-node-tree1"></span>&nbsp;&nbsp;{per_title}</a></dd>
    """
    final_html = """<li class="layui-nav-item">
                    <a href="javascript:;"><span class="iconfont icon-zhuye"></span>&nbsp;&nbsp;首页</a>
                </li>"""
    permission_html = ''
    menu_html = ''
    # for menu in menu_data:
    for num in range(len(menu_data)):
        menu_html += menu_str.format(menu_icon=menu_data[num]['icon'], menu_title=menu_data[num]['title'])
        # for item in permission_data:
        final_html += '<li class="layui-nav-item">' + menu_html + '<dl class="layui-nav-child">'
        menu_html = ''
        for n in range(len(permission_data)):
            if permission_data[n]['menu_id'] == menu_data[num]['id']:
                permission_html += permission_str.format(
                    per_url=permission_data[n]['url'],
                    per_id=permission_data[n]['per_id'],
                    per_title=permission_data[n]['title'])
                final_html += permission_html
                permission_html = ''
                if n == len(permission_data) - 1:
                    final_html += '</dl></li>'
            else:
                if n == len(permission_data) - 1:
                    final_html += '</dl></li>'
                    break
                elif n < len(permission_data) - 1:
                    continue
    return mark_safe(final_html)        # 返回字符串用mark_safe，否则传到模板会转义


if __name__ == '__main__':
    permitions = [
        {'title': '菜单管理', 'url': '/hospital_client/menuManage/home/', 'menu_id': 1, 'per_id': 'menu_manage'},
        {'title': '用户管理', 'url': '/hospital_client/userManage/home/', 'menu_id': 1, 'per_id': 'user_manage'},
        {'title': '角色管理', 'url': '/hospital_client/roleManage/home/', 'menu_id': 1, 'per_id': 'role_manage'},
        {'title': '机构管理', 'url': '/hospital_client/companyManage/home', 'menu_id': 1, 'per_id': 'company_manage'},
        {'title': '处方笺', 'url': '/hospital_client/prescriptionMake/firstStep', 'menu_id': 6, 'per_id': 'prescription_make'},
        {'title': '订单列表查询', 'url': '/hospital_client/orderListQuery/home', 'menu_id': 6, 'per_id': 'order_lists_query'},
        {'title': '药品管理', 'url': '/hospital_client/drugsManage/home', 'menu_id': 9, 'per_id': 'drugs_manage'},
        {'title': '添加药品', 'url': '/hospital_client/addDrugs', 'menu_id': 9, 'per_id': 'add_drugs'},
        {'title': '药材批量导入', 'url': '/hospital_client/batchImportDrugs', 'menu_id': 9, 'per_id': 'batch_import_drugs'},
        {'title': '医院对账处方清单', 'url': '/hospital_client/statementsManage/reconciliation', 'menu_id': 13, 'per_id': 'reconciliation'},
        {'title': '处方销售统计报表', 'url': '/hospital_client/statementsManage/presSalesCount', 'menu_id': 13, 'per_id': 'pres_sales_count'},
        {'title': '药材销售统计报表', 'url': '/hospital_client/statementsManage/drugsSalesCount', 'menu_id': 13, 'per_id': 'drugs_sales_count'},
        {'title': '处方查询', 'url': '/hospital_client/prescriptionQuery', 'menu_id': 6, 'per_id': 'prescription_query'}]
    menu_list = [
        {'id': 1, 'title': '系统管理', 'icon': 'iconfont icon-xitongguanli2'},
        {'id': 6, 'title': '订单管理', 'icon': 'iconfont icon-chanpinguanli2'},
        {'id': 9, 'title': '数据管理', 'icon': 'iconfont icon-chanpinguanli2'},
        {'id': 13, 'title': '报表管理', 'icon': 'iconfont icon-jiesuantongjibiao'}]
    print(get_menu_html(menu_list, permission_data=permitions))
