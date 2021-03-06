# coding:utf-8
"""
  Time : 2021/2/14 下午3:25
  Author : vincent
  FileName: prescriptionServices
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2021/2/14 下午3:25
"""
import logging
import urllib

from suds.client import Client
import time

from requires.handle import md5_creat_password, get_config, Envelope, response_base64_decode, request_base64_encode
logger = logging.getLogger('log')


def upload_prescription(order, pres, pres_details, company):
    request_sb = build_upload_prescription_req(order, pres, pres_details, company)
    url = get_config('interface', 'orderUrl')
    logger.info("调用智慧药房接口saveOrderInfo Begin, 请求url：%s, 请求体：%s" % (url, request_sb))
    # 使用 suds 调用 webservice 接口保存订单
    request_body = request_base64_encode(request_sb)
    logger.info('request_body:%s' % request_body)
    try:
        client = Client(url)
    except urllib.error.URLError as e:
        return {'message': '接口异常！' + str(e)}
    response = client.service.saveOrderInfo(request_body)
    logger.info("调用智慧药房接口saveOrderInfo End, 接口返回：%s", response_base64_decode(response))
    decode_response = response_base64_decode(response)
    xml = Envelope(decode_response)
    if xml.get_context("resultCode") == '0':
        order_id = xml.get_context("orderid")
        description = xml.get_context('description')
        return {'orderId': order_id, 'message': description}
    elif xml.get_context("resultCode") == '22':
        return {'specialCode': '22', 'message': xml.get_context('description')}
    else:
        reason = xml.get_context('description')
        return {'message': reason}


def build_upload_prescription_req(order, pres, pres_details, company):
    """
    组装请求报文
    :param company:
    :param pres_details:
    :param order:
    :param pres:
    :return:
    """
    key = int(time.time() * 1000)
    sign = md5_creat_password("saveOrderInfo" + str(key) + md5_creat_password(company.company_password))
    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    content += "<orderInfo>"
    content += "<head>"
    content += "<company_num>" + company.company_code + "</company_num>"
    content += "<key>" + str(key) + "</key>"
    content += "<sign>" + sign + "</sign>"
    content += "</head>"
    content += "<data>"
    content += "<order_time>" + order.order_time + "</order_time>"
    content += "<treat_card>" + order.treat_card + "</treat_card>"
    content += "<reg_num>" + order.reg_num + "</reg_num>"
    content += "<addr_str>" + order.provinces + "," + order.city + "," + order.zone + "," + order.addr_str + "</addr_str>"
    content += "<consignee>" + order.consignee + "</consignee>"
    content += "<con_tel>" + order.con_tel + "</con_tel>"
    content += "<send_goods_time>" + (order.send_goods_time if order.send_goods_time else '') + "</send_goods_time>"
    content += "<is_hos_addr>" + str(order.is_hos_addr) + "</is_hos_addr>"
    content += "<prescript>"
    content += "<pdetail>"
    content += "<user_name>" + pres.user_name + "</user_name>"
    content += "<doctor>" + pres.doctor + "</doctor>"
    content += "<age>" + str(pres.age) + "</age>"
    content += "<gender>" + str(pres.gender) + "</gender>"
    content += "<tel>" + pres.tel + "</tel>"
    content += "<is_suffering>" + str(pres.is_suffering) + "</is_suffering>"
    content += "<amount>" + str(pres.amount) + "</amount>"
    content += "<suffering_num>" + str(pres.suffering_num) + "</suffering_num>"
    content += "<ji_fried>" + str(pres.ji_fried) + "</ji_fried>"
    content += "<per_pack_num>" + str(pres.per_pack_num) + "</per_pack_num>"
    content += "<per_pack_dose>" + (str(pres.per_pack_dose) if pres.per_pack_dose else '200') + "</per_pack_dose>"
    content += "<type>" + str(pres.prescri_type) + "</type>"
    content += "<other_pres_num>" + pres.prescri_id + "</other_pres_num>"
    content += "<special_instru>" + pres.special_instru + "</special_instru>"
    content += "<is_within>" + str(pres.is_within) + "</is_within>"
    content += "<bed_num>" + (str(pres.bed_num) if pres.bed_num else '') + "</bed_num>"
    content += "<hos_depart>" + (pres.hos_depart if pres.hos_depart else '') + "</hos_depart>"
    content += "<hospital_num>" + (pres.hospital_num if pres.hospital_num else '') + "</hospital_num>"
    content += "<disease_code>" + (pres.disease_code if pres.disease_code else '') + "</disease_code>"
    content += "<prescript_remark>" + (pres.prescript_remark if pres.prescript_remark else '') + "</prescript_remark>"
    content += "<medication_methods>" + (pres.medication_methods if pres.medication_methods else '') + \
               "</medication_methods>"
    content += "<medication_instruction>" + \
               (pres.medication_instruction if pres.medication_instruction else '') + "</medication_instruction>"
    content += "<is_hos>" + str(pres.is_hos) + "</is_hos>"
    content += "<medici_xq>"
    for pres_det in pres_details:
        content += "<xq>"
        content += "<medicines>" + pres_det.medicines + "</medicines>"
        content += "<dose>" + pres_det.dose + "</dose>"
        content += "<unit>" + pres_det.unit + "</unit>"
        content += "<goods_num>" + pres_det.drugs_num + "</goods_num>"
        content += "<unit_price>" + (str(pres_det.unit_price) if pres_det.unit_price else '') + "</unit_price>"
        content += "<remark>" + (pres_det.remark if pres_det.remark else '') + "</remark>"
        content += "<m_usage>" + (pres_det.m_usage if pres_det.m_usage else '') + "</m_usage>"
        content += "</xq>"
    content += "</medici_xq>"
    content += "</pdetail>"
    content += "</prescript>"
    content += "</data>"
    content += "</orderInfo>"
    return content


def cancel(op_name, reason, order_id, company):
    """
    取消订单
    :param op_name:
    :param reason:
    :param order_id:
    :param company:
    :return:
    """
    request_sb = build_cancel_order_rq(op_name, reason, order_id, company)
    url = get_config('interface', 'orderUrl')
    logger.info("调用智慧药房接口cancelOrder Begin, 请求url：%s, 请求体：%s" % (url, request_sb))
    # 使用 suds 调用 webservice 接口保存订单
    request_body = request_base64_encode(request_sb)
    logger.info('request_body:%s' % request_body)
    try:
        client = Client(url)
    except urllib.error.URLError as e:
        return {'message': '接口异常！' + str(e)}
    response = client.service.cancelOrder(request_body)
    logger.info("调用智慧药房接口cancelOrder End, 接口返回：%s", response_base64_decode(response))
    decode_response = response_base64_decode(response)
    xml = Envelope(decode_response)
    try:
        if xml.get_context("status") == 'success':
            return {'status': 'success', 'message': '成功'}
        elif xml.get_context('status') == 'fail':
            message = xml.get_context('message')
            return {'status': 'fail', 'message': message}
    except IndexError:
        reason = xml.get_context('description')
        return {'message': reason}


def build_cancel_order_rq(op_name, reason, order_id, company):
    """
    取消订单报文创建
    :param op_name: 取消订单操作人
    :param reason: 取消订单原因
    :param order_id: 取消的目标订单号(智慧药房订单号)
    :param company: 订单所属机构
    :return:
    """
    key = int(time.time() * 1000)
    sign = md5_creat_password("cancelOrder" + str(key) + md5_creat_password(company.company_password))
    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    content += "<orderInfo>"
    content += "<head>"
    content += "<company_num>" + company.company_code + "</company_num>"
    content += "<key>" + str(key) + "</key>"
    content += "<sign>" + sign + "</sign>"
    content += "</head>"
    content += "<data>"
    content += "<operate_name>" + op_name + "</operate_name>"
    content += "<reason>" + reason + "</reason>"
    content += "<order_id>" + order_id + "</order_id>"
    content += "</data>"
    content += "</orderInfo>"
    return content

