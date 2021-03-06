# coding:utf-8
"""
  Time : 2021/2/14 下午8:22
  Author : vincent
  FileName: test
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2021/2/14 下午8:22
"""
from suds.client import Client
import xml.etree.cElementTree as ET


class XmlEnvelopeTree(object):
    """ Xml Envelope Tree parser """
    def __init__(self, envString):
        if isinstance(envString, dict):
            node_list = []
            for key, value in envString.items():
                node = ET.Element(key)
                node.text = str(value)
                node_list.append(node)
            root = ET.Element('result')  # 创建根节点
            root.extend(node_list)
            self.root = root
            self.tree = ET.ElementTree(root)
        elif isinstance(envString, str):
            self.root = ET.fromstring(envString)

    def xml_to_dict(self):
        """ parse Xml Envelope to dict """
        medicine_node = ['medicines', 'dose', 'unit', 'unit_price', 'goods_num', 'dose_that',
                         'remark', 'm_usage', 'goods_norms', 'goods_orgin', 'MedPerDos', 'MedPerDay']
        dict_data = {}
        n = 0
        xq_childs = 0
        for child in self.root.iter():
            # print(child.tag)
            # print(child.text)
            if child.tag not in medicine_node:
                if child.tag == 'xq':
                    xq_childs = child.__len__()     # __len__：返回元素大小，元素的大小为元素的子元素数量
                dict_data[child.tag] = child.text
            else:
                if n < xq_childs:
                    dict_data[child.tag] = [child.text]
                    n += 1
                else:
                    dict_data[child.tag].append(child.text)
        return dict_data

    def envelope_encode(self):
        data = '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(self.root, encoding='utf-8').decode()
        return data


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
    print(final_html)
    # return mark_safe(final_html)        # 返回字符串用mark_safe，否则传到模板会转义


if __name__ == '__main__':
    url = 'http://120.79.173.198/OrderServices/?wsdl'
    rq_decode = """<?xml version="1.0" encoding="UTF-8"?><orderInfo><head><company_num>10000</company_num><key>1613310073394</key><sign>3F4393E15C11AB9B9D72B1BC82488A02</sign></head><data><order_time>2021-02-14 21:39:44</order_time><treat_card>338116</treat_card><reg_num>202102149025729</reg_num><addr_str>云南省,昆明市,官渡区,官渡广场旁官渡区人民医院 </addr_str><consignee>拉布拉多</consignee><con_tel>16785894378</con_tel><send_goods_time>2021-02-16</send_goods_time><is_hos_addr>2</is_hos_addr><prescript><pdetail><user_name>嚣张２号</user_name><doctor>vincent</doctor><age>23</age><gender>1</gender><tel>18907897658</tel><is_suffering>1</is_suffering><amount>3</amount><suffering_num>9</suffering_num><ji_fried>1</ji_fried><per_pack_num>3</per_pack_num><per_pack_dose>200</per_pack_dose><type>0</type><other_pres_num>1613309853</other_pres_num><special_instru>上呼吸道感染</special_instru><is_within>0</is_within><bed_num>25</bed_num><hos_depart>中西医结合科</hos_depart><hospital_num>27364759673</hospital_num><disease_code>09807</disease_code><prescript_remark>加５g生姜</prescript_remark><medication_methods></medication_methods><medication_instruction>每天３次，每次1袋</medication_instruction><is_hos>0</is_hos><medici_xq><xq><medicines>白茅根</medicines><dose>11</dose><unit>g</unit><goods_num>010104</goods_num><unit_price>0.12370</unit_price><remark></remark><m_usage></m_usage></xq><xq><medicines>白芍</medicines><dose>15</dose><unit>g</unit><goods_num>010606</goods_num><unit_price>0.05000</unit_price><remark></remark><m_usage></m_usage></xq><xq><medicines>白术</medicines><dose>30</dose><unit>g</unit><goods_num>010306</goods_num><unit_price>0.07100</unit_price><remark></remark><m_usage></m_usage></xq><xq><medicines>砂仁</medicines><dose>6</dose><unit>g</unit><goods_num>030603</goods_num><unit_price>0.45200</unit_price><remark></remark><m_usage>先煎</m_usage></xq><xq><medicines>薄荷</medicines><dose>8</dose><unit>g</unit><goods_num>011007</goods_num><unit_price>0.04700</unit_price><remark></remark><m_usage>后下</m_usage></xq><xq><medicines>胆南星</medicines><dose>3</dose><unit>g</unit><goods_num>030201</goods_num><unit_price>0.04700</unit_price><remark>有毒</remark><m_usage>包煎</m_usage></xq><xq><medicines>甘草片</medicines><dose>2</dose><unit>g</unit><goods_num>010205</goods_num><unit_price>0.09400</unit_price><remark>泡服</remark><m_usage>后下</m_usage></xq></medici_xq></pdetail></prescript></data></orderInfo>"""
    client = Client(url)
    # print(client)
    env_tree = XmlEnvelopeTree(rq_decode)
    print(env_tree)
    dict_data = env_tree.xml_to_dict()
    print(dict_data)
    permitions = [
        {'title': '菜单管理', 'url': '/hospital_client/menuManage/home/', 'menu_id': 1, 'per_id': 'menu_manage'},
        {'title': '用户管理', 'url': '/hospital_client/userManage/home/', 'menu_id': 1, 'per_id': 'user_manage'},
        {'title': '角色管理', 'url': '/hospital_client/roleManage/home/', 'menu_id': 1, 'per_id': 'role_manage'},
        {'title': '机构管理', 'url': '/hospital_client/companyManage/home', 'menu_id': 1, 'per_id': 'company_manage'},
        {'title': '处方笺', 'url': '/hospital_client/prescriptionMake/firstStep', 'menu_id': 6,
         'per_id': 'prescription_make'},
        {'title': '订单列表查询', 'url': '/hospital_client/orderListQuery/home', 'menu_id': 6, 'per_id': 'order_lists_query'},
        {'title': '药品管理', 'url': '/hospital_client/drugsManage/home', 'menu_id': 9, 'per_id': 'drugs_manage'},
        {'title': '添加药品', 'url': '/hospital_client/addDrugs', 'menu_id': 9, 'per_id': 'add_drugs'},
        {'title': '药材批量导入', 'url': '/hospital_client/batchImportDrugs', 'menu_id': 9, 'per_id': 'batch_import_drugs'},
        {'title': '医院对账处方清单', 'url': '/hospital_client/statementsManage/reconciliation', 'menu_id': 13,
         'per_id': 'reconciliation'},
        {'title': '处方销售统计报表', 'url': '/hospital_client/statementsManage/presSalesCount', 'menu_id': 13,
         'per_id': 'pres_sales_count'},
        {'title': '药材销售统计报表', 'url': '/hospital_client/statementsManage/drugsSalesCount', 'menu_id': 13,
         'per_id': 'drugs_sales_count'},
        {'title': '处方查询', 'url': '/hospital_client/prescriptionQuery', 'menu_id': 6, 'per_id': 'prescription_query'}]
    menu_list = [
        {'id': 1, 'title': '系统管理', 'icon': 'iconfont icon-xitongguanli2'},
        {'id': 6, 'title': '订单管理', 'icon': 'iconfont icon-chanpinguanli2'},
        {'id': 9, 'title': '数据管理', 'icon': 'iconfont icon-chanpinguanli2'},
        {'id': 13, 'title': '报表管理', 'icon': 'iconfont icon-jiesuantongjibiao'}]
    get_menu_html(menu_list, permission_data=permitions)
